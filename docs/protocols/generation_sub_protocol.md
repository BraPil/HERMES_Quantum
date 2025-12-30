# Generation Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs all code, documentation, and file generation within HERMES_Quantum. It ensures consistent quality, maintainability, and adherence to project standards.

---

## 🎯 Core Principle

**Special characters and emojis are STRICTLY FORBIDDEN in this workspace and on this project in its entirety. Ensure that special characters and emojis are NEVER used unless expressly necessary, then get authorization first.**

---

## 🚨 CRITICAL GENERATION RULES

### ABSOLUTELY FORBIDDEN (Without Explicit Authorization)

1. **Special Characters** in code or documentation
2. **Emojis** anywhere in the project
3. **Non-standard encoding** characters
4. **Decorative symbols** or Unicode art

### ALWAYS REQUIRED

1. **Complete documentation** for all generated code
2. **Type hints** in Python code
3. **Error handling** for all operations
4. **Logging** for significant actions
5. **Testing** considerations documented

---

## 📋 Generation Procedure

### Step 1: Pre-Generation Planning

1. **Understand Requirements**
   - What exactly needs to be generated?
   - What is its purpose?
   - How will it integrate with existing code?
   - What are the success criteria?

2. **Review Existing Code**
   - Check existing patterns and conventions
   - Identify reusable components
   - Understand current architecture
   - Follow established patterns

3. **Check Dependencies**
   - What imports are needed?
   - Are all dependencies available?
   - Are versions compatible?
   - Document any new dependencies

### Step 2: Design Before Generating

1. **Plan Structure**
   - Outline classes and functions needed
   - Design data structures
   - Plan error handling
   - Consider edge cases

2. **Review Standards**
   - Consult [master_protocol.md](../../master_protocol.md) code standards
   - Follow Python PEP 8 guidelines
   - Match existing code style
   - Verify naming conventions

3. **Document Plan**
   - Write generation plan in log
   - Get confirmation if needed
   - Note any risks or concerns

### Step 3: Generate Code/Files

1. **Follow Standards**
   ```python
   # CORRECT: Clean, documented, type-hinted Python
   def analyze_stock_data(symbol: str, data: pd.DataFrame) -> dict:
       """
       Analyze stock data for a given symbol.
       
       Args:
           symbol: Stock ticker symbol (e.g., 'QBTS')
           data: DataFrame with columns [date, open, high, low, close, volume]
           
       Returns:
           Dictionary containing analysis results
           
       Raises:
           ValueError: If data is empty or missing required columns
       """
       if data.empty:
           raise ValueError("Data cannot be empty")
       
       # Analysis logic here
       results = {
           "symbol": symbol,
           "mean_close": data['close'].mean(),
           "volatility": data['close'].std()
       }
       
       return results
   ```

2. **FORBIDDEN Patterns**
   ```python
   # WRONG: Special characters/emojis
   def analyze_stock_data_📊(symbol: str) -> dict:  # ❌ FORBIDDEN
       """Analyze stock data 🚀"""  # ❌ FORBIDDEN
       return {"status": "✅"}  # ❌ FORBIDDEN
   
   # WRONG: No documentation
   def process(x):  # ❌ No docstring, no type hints
       return x * 2  # ❌ No explanation
   
   # WRONG: Poor naming
   def f(d):  # ❌ Unclear names
       return d  # ❌ No purpose
   ```

3. **Include Required Elements**
   - File header with description
   - Imports organized properly
   - Type hints for all functions
   - Comprehensive docstrings
   - Error handling
   - Logging where appropriate
   - Tests or test stubs

### Step 4: Document Generated Code

1. **File-Level Documentation**
   ```python
   """
   Module: agent_orchestrator.py
   
   Purpose: Coordinates communication between specialized analysis agents
   
   Dependencies:
       - agents.analyst: Financial analysis agent
       - agents.psychology: Market sentiment agent
       - core.messaging: Inter-agent messaging system
       
   Usage:
       orchestrator = AgentOrchestrator()
       results = orchestrator.coordinate_analysis('QBTS')
   
   Author: HERMES_Quantum System
   Created: 2025-12-28
   """
   ```

2. **Function/Method Documentation**
   - Clear purpose statement
   - Parameter descriptions with types
   - Return value description
   - Exceptions that may be raised
   - Usage examples if complex

3. **Class Documentation**
   - Class purpose and responsibility
   - Attribute descriptions
   - Method overview
   - Usage examples

### Step 5: Validate Generated Code

1. **Self-Review Checklist**
   - [ ] No special characters or emojis
   - [ ] All functions have type hints
   - [ ] All functions have docstrings
   - [ ] Error handling implemented
   - [ ] Logging added where needed
   - [ ] Imports are correct and organized
   - [ ] Naming is clear and consistent
   - [ ] Code follows existing patterns
   - [ ] Edge cases considered

2. **Test Considerations**
   - What should be tested?
   - What are edge cases?
   - What are error conditions?
   - Document test requirements

### Step 6: Log Generation

1. **Create Generation Log**
   - Follow naming: `Generation_[Description]_[YYYY-MM-DD]_[HHMM].md`
   - Save to: `logs/generation/`
   - Update [master_log.md](../../master_log.md)

2. **Document**
   - What was generated
   - Why it was generated
   - How it fits into system
   - Any concerns or notes
   - Testing requirements

---

## ✅ Generation Checklist

Before considering generation complete:

- [ ] Requirements fully understood
- [ ] Existing code patterns reviewed
- [ ] Design planned and documented
- [ ] Code generated with all required elements
- [ ] NO special characters or emojis used
- [ ] All functions have type hints and docstrings
- [ ] Error handling implemented
- [ ] Code follows project standards
- [ ] Self-review completed
- [ ] Generation log created
- [ ] master_log.md updated
- [ ] Code is well researched, thought out and organized

---

## 🎨 Code Style Standards

### Python Standards (PEP 8 Compliant)

```python
# Imports: Standard library, third-party, local (in that order)
import os
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from agents.base import BaseAgent
from core.config import Config


# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30


# Classes: PascalCase
class StockAnalyzer:
    """
    Analyzes stock data for quantum computing companies.
    
    Attributes:
        symbols: List of stock symbols to analyze
        config: Configuration object
    """
    
    def __init__(self, symbols: List[str], config: Config) -> None:
        """Initialize the analyzer with symbols and config."""
        self.symbols = symbols
        self.config = config
    
    # Methods: snake_case
    def analyze_symbol(self, symbol: str) -> Dict[str, float]:
        """Analyze a single stock symbol."""
        pass


# Functions: snake_case
def calculate_volatility(prices: pd.Series) -> float:
    """Calculate price volatility using standard deviation."""
    return prices.std()


# Variables: snake_case
stock_data = pd.DataFrame()
analysis_results = {}
```

### Documentation Standards

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[Dict] = None
) -> tuple[bool, str]:
    """
    One-line summary of what function does.
    
    Longer description if needed, explaining the purpose,
    behavior, and any important details about the function.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter  
        param3: Optional parameter description. Defaults to None.
    
    Returns:
        Tuple of (success_flag, message) where:
            success_flag: True if operation succeeded
            message: Status message or error description
    
    Raises:
        ValueError: If param2 is negative
        ConnectionError: If unable to reach data source
    
    Example:
        >>> success, msg = complex_function("QBTS", 100)
        >>> if success:
        ...     print(msg)
    """
    pass
```

---

## 📊 Generation Output Template

```markdown
# Generation Log: [What Was Generated]

**Date**: YYYY-MM-DD HH:MM
**Generator**: [Name/System]
**Type**: [Code/Documentation/Config/Other]
**Status**: Complete

## Generation Summary
[Brief description of what was generated and why]

## Requirements
[What requirements this generation fulfills]

## Design Decisions
1. [Decision 1 and rationale]
2. [Decision 2 and rationale]

## Files Generated
- `path/to/file1.py`: [Description]
- `path/to/file2.py`: [Description]

## Key Components
### Component 1
**Purpose**: [What it does]
**Location**: [File and line numbers]
**Dependencies**: [What it depends on]

## Integration Points
[How generated code integrates with existing system]

## Testing Requirements
1. [Test case 1]
2. [Test case 2]

## Known Limitations
[Any limitations or technical debt]

## Next Steps
- [ ] Write tests
- [ ] Integration testing
- [ ] Documentation review

## Code Review Checklist
- [x] No special characters/emojis
- [x] Type hints present
- [x] Docstrings complete
- [x] Error handling implemented
- [x] Follows project standards
```

---

## 🔗 Related Protocols

- **Analyzing existing code?** → [analysis_sub_protocol.md](analysis_sub_protocol.md)
- **Researching approaches?** → [research_sub_protocol.md](research_sub_protocol.md)
- **Logging generation?** → [logging_sub_protocol.md](logging_sub_protocol.md)

---

## 📈 Quality Indicators

High-quality generated code exhibits:
- Clear, self-documenting names
- Complete documentation
- Proper error handling
- Consistent with existing code
- Well-tested or testable
- Maintainable and extensible
- No forbidden elements (emojis, special chars)

---

**Remember**: Generation quality directly impacts system maintainability. Never rush generation. Always follow standards. Always document. Always get authorization for special characters.

---

**END OF GENERATION SUB-PROTOCOL**
