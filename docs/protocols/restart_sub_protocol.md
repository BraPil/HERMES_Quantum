# Restart Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs the process of preparing for and executing a context window restart, ensuring no work or context is lost during the transition.

---

## 🎯 Core Principle

**When context window is near capacity or becoming unstable, prepare for restart by ensuring all work is logged, summarized, and a comprehensive restart prompt is created.**

---

## 🚨 When to Restart

### Indicators That Restart Is Needed

1. **Performance Degradation**
   - Responses becoming slower
   - Increased errors or inconsistencies
   - Tool calls failing unexpectedly

2. **Context Issues**
   - Forgetting earlier conversation details
   - Inconsistent with previous decisions
   - Unable to recall recent work

3. **Window Capacity**
   - Long conversation thread
   - Many files read/edited
   - Extensive research performed

4. **Planned Restart**
   - End of work session
   - Before major milestone
   - Transitioning to new task

### User Signals

- User says "prepare for restart"
- User says "engage restart protocol"
- User says "let's restart the conversation"

---

## 📋 Restart Preparation Procedure

### Step 1: Acknowledge Restart Request

```markdown
Understood. Engaging restart_sub_protocol.md. I will:
1. Review entire chat history
2. Ensure all work is properly logged
3. Verify all indexes are current
4. Consult Overall Plan and assess progress
5. Create comprehensive restart prompt

Beginning restart preparation...
```

### Step 2: Comprehensive Chat History Review

1. **Review Every Exchange**
   - Read through ENTIRE conversation
   - No sampling - review EVERY message
   - Note all significant activities
   - Identify all decisions made
   - Track all files modified

2. **Categorize Activities**
   - Analysis performed
   - Research conducted
   - Code generated
   - Problems solved
   - Decisions made
   - Tasks completed

3. **Verify Logging**
   - Check each activity has log entry
   - Verify logs are complete and detailed
   - Ensure all files are documented
   - Confirm all decisions are recorded

### Step 3: Ensure Complete Logging

1. **Create Missing Logs**
   - If any work isn't logged, log it now
   - Follow [logging_sub_protocol.md](logging_sub_protocol.md)
   - Be thorough and comprehensive

2. **Update Existing Logs**
   - Bring all logs up to current state
   - Update statuses
   - Add final entries

3. **Organize Logs**
   - Ensure proper naming
   - Verify correct directories
   - Check completeness

### Step 4: Update All Indexes

1. **Update master_log.md**
   - Add any new logs
   - Update all "Last Updated" timestamps
   - Update all statuses
   - Verify index is complete and accurate

2. **Update master_protocol.md**
   - Update any indexes (tools, references)
   - Update progress tracking
   - Note any protocol changes
   - Update version history if needed

3. **Verify Workspace State**
   - Check all files are saved
   - Verify no uncommitted changes (if using git)
   - Ensure all outputs are preserved

### Step 5: Consult Overall Plan

1. **Review Project Plan**
   - Check MASTER_PLAN.md or equivalent
   - Understand overall goals and milestones
   - Note current phase

2. **Assess Progress**
   - **Where We Are**: Current state
   - **Where We Came From**: Recent progress
   - **Where We're Going**: Next objectives

3. **Identify Next Steps**
   - Immediate priorities
   - Upcoming tasks
   - Any blockers
   - Required resources

### Step 6: Create Comprehensive Summary

1. **Session Summary**
   ```markdown
   ## Session Summary
   
   **Duration**: [Start time to now]
   **Focus Areas**: [Main areas worked on]
   **Major Accomplishments**: [Key achievements]
   
   ### Work Completed
   1. [Completed item 1 with details]
   2. [Completed item 2 with details]
   
   ### Work In Progress
   1. [In progress item 1] - Status: [X%]
      - [What's done]
      - [What remains]
   2. [In progress item 2] - Status: [X%]
      - [What's done]
      - [What remains]
   
   ### Important Decisions Made
   1. [Decision 1] - Rationale: [Why]
   2. [Decision 2] - Rationale: [Why]
   
   ### Files Modified
   - `path/to/file1.py`: [Changes made]
   - `path/to/file2.md`: [Changes made]
   
   ### Challenges Encountered
   1. [Challenge 1] - Resolution: [How solved]
   2. [Challenge 2] - Resolution: [How solved]
   ```

2. **Current State Documentation**
   ```markdown
   ## Current Project State
   
   ### Overall Progress
   - Phase: [Current phase]
   - Completion: [X%]
   - Status: [On Track/Ahead/Behind/Blocked]
   
   ### Component Status
   | Component | Status | Notes |
   |-----------|--------|-------|
   | [Component 1] | [Status] | [Details] |
   | [Component 2] | [Status] | [Details] |
   
   ### Recent Changes
   [Summary of recent work and its impact]
   
   ### Known Issues
   1. [Issue 1] - Severity: [X] - Status: [Y]
   2. [Issue 2] - Severity: [X] - Status: [Y]
   ```

3. **Context Preservation**
   ```markdown
   ## Critical Context
   
   ### Active Conventions
   - [Convention 1]: [Description]
   - [Convention 2]: [Description]
   
   ### Key Patterns Established
   - [Pattern 1]: [Where used and why]
   - [Pattern 2]: [Where used and why]
   
   ### Important Constraints
   - [Constraint 1]: [Details]
   - [Constraint 2]: [Details]
   
   ### Ongoing Considerations
   - [Consideration 1]: [Why it matters]
   - [Consideration 2]: [Why it matters]
   ```

### Step 7: Create Restart Prompt

1. **Build Comprehensive Restart Prompt**

```markdown
# HERMES_Quantum Restart Context

## Quick Start
I'm continuing work on HERMES_Quantum, a multi-agent AI system for quantum computing stock analysis. Review the protocol system and current state below.

## Protocol System (CRITICAL - Read First)
- **copilot-instructions.md**: Main instructions and protocol hierarchy
- **master_protocol.md**: Central command with prime directive and sub-protocols
- **master_log.md**: Index of all logs and current status

**Prime Directive**: Build and maintain a comprehensive, multi-agent AI system that provides 100% complete analysis of quantum computing stocks (QBTS, IONQ, RGTI, QUBT). Every component must be fully documented, mapped, and understood.

## Current Status

### Project Phase
[Current phase and overall completion percentage]

### Recent Work Completed
1. [Accomplishment 1 with context]
2. [Accomplishment 2 with context]
3. [Accomplishment 3 with context]

### Current Focus
[What we're currently working on and why]

### Work In Progress
1. **[Task 1]** - [X%] complete
   - Done: [What's finished]
   - Remaining: [What's left]
   - Next step: [Immediate next action]

2. **[Task 2]** - [X%] complete
   - [Same structure]

## Important Files Index

### Protocol Files (Read These First)
- [copilot-instructions.md](copilot-instructions.md)
- [master_protocol.md](master_protocol.md)
- [master_log.md](master_log.md)

### Sub-Protocols
- [analysis_sub_protocol.md](docs/protocols/analysis_sub_protocol.md)
- [research_sub_protocol.md](docs/protocols/research_sub_protocol.md)
- [generation_sub_protocol.md](docs/protocols/generation_sub_protocol.md)
- [logging_sub_protocol.md](docs/protocols/logging_sub_protocol.md)
- [tool_identification_sub_protocol.md](docs/protocols/tool_identification_sub_protocol.md)
- [reference_material_identification_sub_protocol.md](docs/protocols/reference_material_identification_sub_protocol.md)
- [tool_and_reference_material_request_sub_protocol.md](docs/protocols/tool_and_reference_material_request_sub_protocol.md)
- [restart_sub_protocol.md](docs/protocols/restart_sub_protocol.md)

### Active Work Files
- [File 1](path): [Current state and purpose]
- [File 2](path): [Current state and purpose]

### Key Reference Files
- [Reference 1](path): [Why important]
- [Reference 2](path): [Why important]

### Recent Logs
- [Log 1](path): [What it contains]
- [Log 2](path): [What it contains]

## Critical Context

### Active Conventions
[Any established patterns or conventions to maintain]

### Important Decisions
[Recent decisions that inform future work]

### Known Issues/Blockers
[Any problems or obstacles]

### Dependencies
[What depends on what]

## Immediate Next Steps

Priority order for continuation:

1. **[Priority 1]**: [Detailed description]
   - Why: [Rationale]
   - How: [Approach]
   - Files: [What to work with]

2. **[Priority 2]**: [Detailed description]
   - Why: [Rationale]
   - How: [Approach]
   - Files: [What to work with]

3. **[Priority 3]**: [Detailed description]
   - Why: [Rationale]
   - How: [Approach]
   - Files: [What to work with]

## Key Reminders

- **Anti-Sampling**: Read EVERY word of EVERY file - no sampling allowed
- **Logging**: Update logs after every significant action
- **Prime Directive**: All work advances complete system understanding
- **No Special Characters**: Strictly forbidden unless authorized

## Request

Please:
1. Read copilot-instructions.md and master_protocol.md completely
2. Review master_log.md to understand current state
3. Verify understanding of context above
4. Confirm next steps
5. Begin with [specific first action]
```

2. **Format for Easy Copy-Paste**
   - Clear sections
   - All links functional
   - No line breaks in middle of concepts
   - Ready to paste as-is

### Step 8: Create Restart Log

1. **Document Restart Preparation**
   - Create log: `Restart_Preparation_[YYYY-MM-DD]_[HHMM].md`
   - Save to: `logs/restart/`
   - Include full summary and restart prompt
   - Update master_log.md

2. **Verify Everything Saved**
   - All files saved
   - All logs created/updated
   - All indexes current
   - Restart prompt ready

### Step 9: Present Restart Prompt

```markdown
## Restart Preparation Complete

I have:
✓ Reviewed entire chat history
✓ Ensured all work is logged
✓ Updated all indexes (master_log.md, master_protocol.md)
✓ Assessed current state and progress
✓ Identified next steps
✓ Created comprehensive restart prompt

**Restart Log**: [Link to restart log]

---

## COPY THIS PROMPT FOR RESTART

[Present the full restart prompt in a clear, copy-able format]

---

You can now restart the conversation. Simply copy the prompt above and paste it into a new conversation window.
```

---

## ✅ Restart Preparation Checklist

- [ ] Restart request acknowledged
- [ ] ENTIRE chat history reviewed (no sampling)
- [ ] All activities identified and categorized
- [ ] ALL work properly logged
- [ ] Missing logs created
- [ ] Existing logs updated to current
- [ ] master_log.md fully updated
- [ ] master_protocol.md updated
- [ ] Overall plan consulted
- [ ] Progress assessed
- [ ] Next steps identified
- [ ] Comprehensive summary created
- [ ] Current state documented
- [ ] Critical context preserved
- [ ] Important files indexed
- [ ] Restart prompt created
- [ ] Restart log created
- [ ] Everything saved and verified
- [ ] Restart prompt presented to user

---

## 🚨 Critical Rules

1. **No Sampling** - Review ENTIRE conversation, not just recent parts
2. **Complete Logging** - Every activity must be logged
3. **Update Everything** - All indexes must be current
4. **Preserve Context** - All important context must be in restart prompt
5. **Be Thorough** - Better to include too much than too little
6. **Test Links** - Verify all file references are correct
7. **Clear Instructions** - Restart prompt must be immediately actionable

---

## 📈 Quality Indicators

Good restart preparation includes:
- Complete review of conversation
- All work logged comprehensively
- All indexes updated
- Clear current state summary
- Comprehensive context preservation
- Detailed next steps
- Well-organized restart prompt
- Easy to copy and use

---

**Remember**: The restart prompt is a new conversation's only connection to previous work. Make it comprehensive, clear, and actionable. Include everything needed to continue seamlessly.

---

**END OF RESTART SUB-PROTOCOL**
