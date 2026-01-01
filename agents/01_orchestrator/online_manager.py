"""
Agent 01: OnlineManager
========================
Multi-agent workflow coordination with DAG-based execution.

Features:
- Workflow DAG definition and execution
- Parallel stage processing
- Graceful degradation on failures
- Task queuing with retry logic
- Real-time status monitoring

Based on Qlib OnlineManager pattern.

Created: 2026-01-01
"""

import asyncio
import logging
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from pathlib import Path
from enum import Enum
import json
from collections import deque

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some tasks failed
    FAILED = "failed"


@dataclass
class Task:
    """Individual task in the workflow."""
    id: str
    agent_id: str
    stage: str
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "stage": self.stage,
            "status": self.status.value,
            "retries": self.retries,
            "error": self.error,
            "duration": self.duration
        }


@dataclass
class Stage:
    """Workflow stage containing one or more tasks."""
    name: str
    agents: List[str]
    parallel: bool = True
    required: bool = True  # If false, failures don't stop workflow
    timeout: int = 300  # Seconds
    tasks: List[Task] = field(default_factory=list)
    status: StageStatus = StageStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agents": self.agents,
            "parallel": self.parallel,
            "required": self.required,
            "status": self.status.value,
            "tasks": [t.to_dict() for t in self.tasks]
        }


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_id: str
    status: str
    stages: List[Stage]
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "duration": self.duration,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "stages": [s.to_dict() for s in self.stages]
        }


class TaskQueue:
    """In-memory task queue with priority support."""
    
    def __init__(self):
        self._queue: deque = deque()
        self._processing: Dict[str, Task] = {}
        self._completed: List[Task] = []
        self._lock = asyncio.Lock()
    
    async def put(self, task: Task, priority: int = 0):
        """Add task to queue."""
        async with self._lock:
            self._queue.append((priority, task))
            # Sort by priority (lower = higher priority)
            self._queue = deque(sorted(self._queue, key=lambda x: x[0]))
    
    async def get(self) -> Optional[Task]:
        """Get next task from queue."""
        async with self._lock:
            if self._queue:
                _, task = self._queue.popleft()
                self._processing[task.id] = task
                return task
            return None
    
    async def complete(self, task_id: str, result: Any = None, error: str = None):
        """Mark task as complete."""
        async with self._lock:
            if task_id in self._processing:
                task = self._processing.pop(task_id)
                if error:
                    task.status = TaskStatus.FAILED
                    task.error = error
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                task.completed_at = datetime.now()
                self._completed.append(task)
    
    async def requeue(self, task_id: str):
        """Requeue a failed task for retry."""
        async with self._lock:
            if task_id in self._processing:
                task = self._processing.pop(task_id)
                task.retries += 1
                task.status = TaskStatus.PENDING
                self._queue.append((task.retries, task))  # Lower priority on retry
    
    @property
    def pending_count(self) -> int:
        return len(self._queue)
    
    @property
    def processing_count(self) -> int:
        return len(self._processing)


class OnlineManager:
    """
    Multi-agent workflow manager with DAG execution.
    
    Usage:
        manager = OnlineManager()
        manager.load_workflow('config/workflow.yaml')
        
        # Register agent handlers
        manager.register_handler('22_psychology', agent_22_handler)
        manager.register_handler('23_social', agent_23_handler)
        
        # Run workflow
        result = await manager.run()
    """
    
    def __init__(
        self,
        config_path: str = None,
        max_concurrent_tasks: int = 5
    ):
        self.stages: List[Stage] = []
        self.handlers: Dict[str, Callable] = {}
        self.task_queue = TaskQueue()
        self.max_concurrent = max_concurrent_tasks
        
        self._workflow_id: Optional[str] = None
        self._status_callbacks: List[Callable] = []
        
        if config_path:
            self.load_workflow(config_path)
        
        logger.info("OnlineManager initialized")
    
    def load_workflow(self, config_path: str):
        """Load workflow configuration from YAML file."""
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Workflow config not found: {config_path}")
            return
        
        with open(path) as f:
            config = yaml.safe_load(f)
        
        self.stages = []
        
        for stage_config in config.get('workflow', []):
            stage = Stage(
                name=stage_config['stage'],
                agents=stage_config.get('agents', []),
                parallel=stage_config.get('parallel', True),
                required=stage_config.get('required', True),
                timeout=stage_config.get('timeout', 300)
            )
            self.stages.append(stage)
        
        logger.info(f"Loaded workflow with {len(self.stages)} stages")
    
    def define_workflow(self, stages: List[Dict[str, Any]]):
        """Define workflow programmatically."""
        self.stages = []
        
        for stage_config in stages:
            stage = Stage(
                name=stage_config['stage'],
                agents=stage_config.get('agents', []),
                parallel=stage_config.get('parallel', True),
                required=stage_config.get('required', True),
                timeout=stage_config.get('timeout', 300)
            )
            self.stages.append(stage)
        
        logger.info(f"Defined workflow with {len(self.stages)} stages")
    
    def register_handler(self, agent_id: str, handler: Callable):
        """Register async handler function for an agent."""
        self.handlers[agent_id] = handler
        logger.debug(f"Registered handler for agent {agent_id}")
    
    def on_status_change(self, callback: Callable):
        """Register callback for status changes."""
        self._status_callbacks.append(callback)
    
    async def _notify_status(self, stage: Stage, task: Task = None):
        """Notify status change callbacks."""
        for callback in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(stage, task)
                else:
                    callback(stage, task)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    async def _execute_task(self, task: Task, context: Dict[str, Any]) -> bool:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        handler = self.handlers.get(task.agent_id)
        
        if not handler:
            logger.warning(f"No handler for agent {task.agent_id}")
            task.status = TaskStatus.SKIPPED
            task.completed_at = datetime.now()
            return True
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(context)
            else:
                result = handler(context)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            
            logger.info(f"Task {task.id} completed in {task.duration:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.error = str(e)
            
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Retrying task {task.id} (attempt {task.retries})")
                return await self._execute_task(task, context)
            
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            return False
    
    async def _execute_stage(
        self,
        stage: Stage,
        context: Dict[str, Any]
    ) -> bool:
        """Execute a stage (may contain parallel tasks)."""
        stage.status = StageStatus.RUNNING
        
        # Create tasks for each agent
        stage.tasks = []
        for agent_id in stage.agents:
            task = Task(
                id=f"{stage.name}_{agent_id}_{datetime.now().strftime('%H%M%S')}",
                agent_id=agent_id,
                stage=stage.name
            )
            stage.tasks.append(task)
        
        logger.info(f"Executing stage '{stage.name}' with {len(stage.tasks)} tasks")
        await self._notify_status(stage)
        
        if stage.parallel:
            # Execute tasks in parallel
            tasks = [
                self._execute_task(task, context)
                for task in stage.tasks
            ]
            
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=stage.timeout
                )
                
                success_count = sum(1 for r in results if r is True)
                
            except asyncio.TimeoutError:
                logger.error(f"Stage '{stage.name}' timed out")
                for task in stage.tasks:
                    if task.status == TaskStatus.RUNNING:
                        task.status = TaskStatus.FAILED
                        task.error = "Timeout"
                        task.completed_at = datetime.now()
                success_count = 0
        else:
            # Execute tasks sequentially
            success_count = 0
            for task in stage.tasks:
                success = await self._execute_task(task, context)
                if success:
                    success_count += 1
                elif stage.required:
                    break  # Stop on first failure if required
        
        # Determine stage status
        if success_count == len(stage.tasks):
            stage.status = StageStatus.COMPLETED
        elif success_count > 0:
            stage.status = StageStatus.PARTIAL
        else:
            stage.status = StageStatus.FAILED
        
        await self._notify_status(stage)
        
        # Return false only if required stage fully failed
        if stage.required and stage.status == StageStatus.FAILED:
            return False
        
        return True
    
    async def run(
        self,
        context: Dict[str, Any] = None
    ) -> WorkflowResult:
        """
        Execute the complete workflow.
        
        Args:
            context: Initial context dict passed to all handlers
            
        Returns:
            WorkflowResult with execution details
        """
        if context is None:
            context = {}
        
        self._workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.now()
        
        logger.info(f"Starting workflow {self._workflow_id}")
        
        workflow_status = "completed"
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        
        for stage in self.stages:
            success = await self._execute_stage(stage, context)
            
            for task in stage.tasks:
                total_tasks += 1
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks += 1
                    # Add task result to context for next stage
                    context[f"{task.agent_id}_result"] = task.result
                elif task.status == TaskStatus.FAILED:
                    failed_tasks += 1
            
            if not success:
                workflow_status = "failed"
                logger.error(f"Workflow stopped at stage '{stage.name}'")
                break
        
        completed_at = datetime.now()
        
        result = WorkflowResult(
            workflow_id=self._workflow_id,
            status=workflow_status,
            stages=self.stages,
            started_at=started_at,
            completed_at=completed_at,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks
        )
        
        logger.info(
            f"Workflow {self._workflow_id} {workflow_status} "
            f"({completed_tasks}/{total_tasks} tasks, {result.duration:.1f}s)"
        )
        
        return result
    
    def handle_task_failure(self, task_id: str, stage: Stage) -> bool:
        """
        Handle task failure with graceful degradation.
        
        Returns True if workflow can continue.
        """
        failed_task = None
        for task in stage.tasks:
            if task.id == task_id:
                failed_task = task
                break
        
        if not failed_task:
            return True
        
        # Check if this failure is critical
        if stage.required:
            # Check if we have enough successful tasks
            success_count = sum(
                1 for t in stage.tasks 
                if t.status == TaskStatus.COMPLETED
            )
            
            # If majority succeeded, continue
            if success_count >= len(stage.tasks) // 2:
                logger.warning(
                    f"Continuing despite {failed_task.agent_id} failure "
                    f"({success_count}/{len(stage.tasks)} tasks succeeded)"
                )
                return True
        
        return not stage.required
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "workflow_id": self._workflow_id,
            "stages": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "tasks": [t.to_dict() for t in s.tasks]
                }
                for s in self.stages
            ]
        }
    
    def generate_report(self, result: WorkflowResult) -> str:
        """Generate workflow execution report."""
        report = f"""
{'='*50}
WORKFLOW EXECUTION REPORT
{'='*50}
Workflow ID: {result.workflow_id}
Status: {result.status.upper()}
Duration: {result.duration:.2f}s

SUMMARY
{'-'*50}
Total Tasks:     {result.total_tasks}
Completed:       {result.completed_tasks}
Failed:          {result.failed_tasks}
Success Rate:    {result.success_rate:.1%}

STAGES
{'-'*50}"""
        
        for stage in result.stages:
            stage_icon = "✅" if stage.status == StageStatus.COMPLETED else (
                "⚠️" if stage.status == StageStatus.PARTIAL else "❌"
            )
            report += f"\n{stage_icon} {stage.name.upper()} ({stage.status.value})"
            
            for task in stage.tasks:
                task_icon = "✓" if task.status == TaskStatus.COMPLETED else "✗"
                duration = f"{task.duration:.2f}s" if task.duration else "N/A"
                report += f"\n   {task_icon} {task.agent_id}: {task.status.value} ({duration})"
                if task.error:
                    report += f" - {task.error}"
        
        report += "\n" + "=" * 50
        
        return report


async def main():
    """Demo OnlineManager functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("Agent 01 - OnlineManager Demo")
    print("="*60)
    
    # Initialize manager
    manager = OnlineManager()
    
    # Define workflow programmatically
    manager.define_workflow([
        {
            "stage": "data_collection",
            "agents": ["91_tools"],
            "parallel": False,
            "required": True
        },
        {
            "stage": "sentiment_analysis",
            "agents": ["22_psychology", "23_social", "24_politics"],
            "parallel": True,
            "required": True
        },
        {
            "stage": "technical_analysis",
            "agents": ["25_market"],
            "parallel": False,
            "required": True
        },
        {
            "stage": "portfolio_optimization",
            "agents": ["11_analyst"],
            "parallel": False,
            "required": True
        },
        {
            "stage": "decision",
            "agents": ["01_orchestrator"],
            "parallel": False,
            "required": True
        }
    ])
    
    # Register mock handlers
    async def mock_data_handler(ctx):
        await asyncio.sleep(0.5)
        return {"prices": {"QBTS": 4.27, "IONQ": 8.15}}
    
    async def mock_sentiment_handler(ctx):
        await asyncio.sleep(0.3)
        return {"sentiment": 0.65, "confidence": 0.8}
    
    async def mock_social_handler(ctx):
        await asyncio.sleep(0.2)
        return {"social_sentiment": 0.72}
    
    async def mock_politics_handler(ctx):
        await asyncio.sleep(0.4)
        return {"policy_impact": 0.55}
    
    async def mock_market_handler(ctx):
        await asyncio.sleep(0.6)
        return {"forecast": [4.30, 4.35, 4.40]}
    
    async def mock_analyst_handler(ctx):
        await asyncio.sleep(0.3)
        return {"weights": {"QBTS": 0.3, "IONQ": 0.25}}
    
    async def mock_decision_handler(ctx):
        await asyncio.sleep(0.2)
        return {"action": "BUY", "ticker": "QBTS", "conviction": 0.75}
    
    # Register handlers
    manager.register_handler("91_tools", mock_data_handler)
    manager.register_handler("22_psychology", mock_sentiment_handler)
    manager.register_handler("23_social", mock_social_handler)
    manager.register_handler("24_politics", mock_politics_handler)
    manager.register_handler("25_market", mock_market_handler)
    manager.register_handler("11_analyst", mock_analyst_handler)
    manager.register_handler("01_orchestrator", mock_decision_handler)
    
    # Status callback
    def on_status(stage, task=None):
        if task:
            print(f"  📌 {stage.name}: {task.agent_id} -> {task.status.value}")
        else:
            print(f"📍 Stage: {stage.name} -> {stage.status.value}")
    
    manager.on_status_change(on_status)
    
    # Run workflow
    print("\n🚀 Running workflow...")
    print("-" * 60)
    
    result = await manager.run(context={"tickers": ["QBTS", "IONQ", "RGTI", "QUBT"]})
    
    # Print report
    print("\n" + manager.generate_report(result))
    
    # Print final decision
    if result.status == "completed":
        decision_result = None
        for stage in result.stages:
            if stage.name == "decision":
                for task in stage.tasks:
                    if task.result:
                        decision_result = task.result
        
        if decision_result:
            print(f"\n🎯 DECISION: {decision_result['action']} {decision_result['ticker']}")
            print(f"   Conviction: {decision_result['conviction']:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
