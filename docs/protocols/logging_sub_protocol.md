# Logging Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs all logging activities within HERMES_Quantum. It ensures complete tracking of all work, decisions, and system changes.

---

## 🎯 Core Principle

**Log everything we do. Every single prompt and prompt response should be logged to a specific issue log or a log that is tracking everything for a particular step. Date and time should be in the markdown file's name. At the end of each prompt response, ensure you have updated all applicable logs.**

---

## 📋 Logging Procedure

### Step 1: Identify Log Type

Determine which type of log(s) this work should be recorded in:

- **Session Log**: General work session tracking
- **Task Log**: Specific task or feature development
- **Issue Log**: Problem resolution and debugging
- **Analysis Log**: Analysis work and findings
- **Research Log**: Research activities and findings
- **Generation Log**: Code/file generation activities
- **Restart Log**: Context restart preparation

### Step 2: Create or Update Log

1. **Check for Existing Log**
   - Review [master_log.md](../../master_log.md)
   - Is there an active log for this work?
   - Should existing log be updated or new log created?

2. **Create New Log If Needed**
   - Follow naming convention: `[Type]_[Description]_[YYYY-MM-DD]_[HHMM].md`
   - Use correct directory: `logs/[type]/`
   - Include all required sections (see templates below)

3. **Update Existing Log If Appropriate**
   - Add new entry with timestamp
   - Update status if changed
   - Add findings or progress notes

### Step 3: Log Entry Structure

Every log entry must include:

```markdown
## Entry: [YYYY-MM-DD HH:MM:SS]

**Activity**: [Brief description of what was done]
**Status**: [In Progress/Completed/Blocked/Pending]

### Details
[Detailed explanation of work performed, decisions made, findings discovered]

### Files Affected
- `path/to/file1.py`: [What was done]
- `path/to/file2.md`: [What was done]

### Decisions Made
1. [Decision description and rationale]
2. [Decision description and rationale]

### Issues Encountered
[Any problems, blockers, or concerns]

### Next Steps
- [ ] Action item 1
- [ ] Action item 2
```

### Step 4: Update Master Log

After creating or updating any log:

1. **Open [master_log.md](../../master_log.md)**
2. **Add new log to appropriate index table** (if new log)
3. **Update "Last Updated" timestamp** for the log
4. **Update status** if it changed
5. **Save master_log.md**

### Step 5: Keep Logs Organized

1. **All logs must live in `logs/` directory**
2. **Use correct subdirectory**:
   - `logs/session/`
   - `logs/tasks/`
   - `logs/issues/`
   - `logs/analysis/`
   - `logs/research/`
   - `logs/generation/`
   - `logs/restart/`
   - `logs/setup/`

3. **Follow naming conventions strictly**

---

## ✅ Logging Checklist

After every significant action or at minimum once per prompt response:

- [ ] Identified appropriate log type(s)
- [ ] Created new log OR updated existing log
- [ ] Included timestamp in entry
- [ ] Documented what was done
- [ ] Documented why it was done
- [ ] Noted any decisions made
- [ ] Listed affected files
- [ ] Noted any issues or concerns
- [ ] Listed next steps
- [ ] Updated master_log.md
- [ ] Saved all changes

---

## 📊 Log Templates

### Session Log Template

```markdown
# Session Log: [Date]

**Date**: YYYY-MM-DD
**Session Start**: HH:MM
**Session End**: HH:MM (or "In Progress")
**Focus**: [What this session is focused on]
**Status**: [Active/Completed]

---

## Session Goals
1. [Goal 1]
2. [Goal 2]

---

## Entry: [HH:MM:SS]

**Activity**: [What was done]
**Duration**: [Approximate time spent]

### Details
[Detailed description]

### Progress
- [x] Completed item
- [ ] In progress item
- [ ] Todo item

### Decisions
[Any decisions made]

### Issues
[Any problems encountered]

---

## Entry: [HH:MM:SS]

[Next entry follows same format]

---

## Session Summary

**Accomplishments**:
- [What was accomplished]

**Blockers**:
- [Any blockers encountered]

**Next Session**:
- [What to focus on next time]
```

### Task Log Template

```markdown
# Task Log: [Task Name]

**Task ID**: [If applicable]
**Created**: YYYY-MM-DD HH:MM
**Last Updated**: YYYY-MM-DD HH:MM
**Status**: [Not Started/In Progress/Blocked/Completed]
**Priority**: [High/Medium/Low]

---

## Task Description
[Clear description of what needs to be done]

## Success Criteria
1. [Criterion 1]
2. [Criterion 2]

## Dependencies
- [Dependency 1]
- [Dependency 2]

---

## Work Log

### Entry: [YYYY-MM-DD HH:MM:SS]

**Activity**: [What was done]
**Time Spent**: [Approximate duration]
**Status**: [Current status]

#### Details
[Detailed description]

#### Files Modified
- `file1.py`: [Changes made]

#### Decisions
[Decisions and rationale]

#### Next Steps
- [ ] Step 1
- [ ] Step 2

---

## Task Completion

**Completed**: [YYYY-MM-DD HH:MM or "Not yet completed"]
**Outcome**: [Final result]
**Lessons Learned**: [Any insights gained]
```

### Issue Log Template

```markdown
# Issue Log: [Issue Description]

**Issue ID**: [If applicable]
**Created**: YYYY-MM-DD HH:MM
**Last Updated**: YYYY-MM-DD HH:MM
**Status**: [Open/Investigating/Resolved/Closed]
**Severity**: [Critical/High/Medium/Low]

---

## Issue Description
[Clear description of the problem]

## Impact
[What is affected and how severely]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Observed behavior]

## Expected Behavior
[What should happen instead]

---

## Investigation Log

### Entry: [YYYY-MM-DD HH:MM:SS]

**Activity**: [Investigation performed]
**Findings**: [What was discovered]

#### Files Examined
- `file1.py` (lines X-Y): [Findings]

#### Tests Performed
- [Test description]: [Result]

#### Hypotheses
1. [Hypothesis and evidence]

---

## Resolution

**Root Cause**: [What caused the issue]

**Solution**: [How it was fixed]

**Files Modified**:
- `file1.py`: [Changes made]

**Testing**:
- [Test performed]: [Result]

**Resolution Date**: YYYY-MM-DD HH:MM

**Lessons Learned**: [Insights for preventing similar issues]
```

### Analysis Log Template

See [analysis_sub_protocol.md](analysis_sub_protocol.md) for complete template.

### Research Log Template

See [research_sub_protocol.md](research_sub_protocol.md) for complete template.

### Generation Log Template

See [generation_sub_protocol.md](generation_sub_protocol.md) for complete template.

### Restart Log Template

```markdown
# Restart Preparation Log: [Date]

**Created**: YYYY-MM-DD HH:MM
**Context Window**: [Current state - e.g., "Near capacity" or "% used"]
**Reason**: [Why restart is needed]

---

## Pre-Restart Checklist

- [ ] All work logged to appropriate logs
- [ ] All logs properly organized and indexed
- [ ] master_log.md fully updated
- [ ] Overall_Plan.md consulted
- [ ] Current status documented
- [ ] Next steps identified
- [ ] Restart prompt prepared

---

## Chat History Review

### Key Activities This Session
1. [Activity 1 summary]
2. [Activity 2 summary]

### Important Decisions
1. [Decision and rationale]
2. [Decision and rationale]

### Work Completed
- [Completed item 1]
- [Completed item 2]

### Work In Progress
- [In progress item 1] - Status: [X%]
- [In progress item 2] - Status: [X%]

---

## Current State Analysis

### Where We Are
[Detailed description of current project state]

### Where We Came From
[Summary of recent progress and journey]

### Where We're Going
[Next phase goals and objectives]

---

## Important Files Index

### Protocol Files
- [copilot-instructions.md](../../copilot-instructions.md)
- [master_protocol.md](../../master_protocol.md)
- [master_log.md](../../master_log.md)

### Active Work Files
- [File 1]: [Current state]
- [File 2]: [Current state]

### Key Reference Files
- [Reference 1]: [Why important]
- [Reference 2]: [Why important]

---

## Next Steps Plan

### Immediate Priorities
1. [Priority 1 with details]
2. [Priority 2 with details]

### Blockers and Concerns
- [Blocker 1 and impact]
- [Concern 1 and mitigation]

---

## Restart Prompt

```
[Comprehensive prompt for user to copy and paste after restart]
[Should include:]
[- Context summary]
[- Current state]
[- Important file references]
[- Next steps]
[- Any critical information needed]
```

---

## Post-Restart Verification

After restart, verify:
- [ ] All context restored
- [ ] Files accessible
- [ ] Protocols understood
- [ ] Next steps clear
```

---

## 🚨 Critical Logging Rules

1. **Log Everything** - Every action, every decision, every discovery
2. **Timestamp Everything** - Always include date and time
3. **Update master_log.md** - ALWAYS after creating/updating logs
4. **End of Response** - Check and update logs before ending response
5. **Organized Storage** - All logs in correct `logs/` subdirectory
6. **Clear Descriptions** - Logs must be understandable later
7. **Status Tracking** - Always update status fields

---

## 📈 Logging Best Practices

1. **Be Specific** - "Fixed bug in analyze_stock()" not "Fixed bug"
2. **Include Context** - Why was decision made? What was tried?
3. **Reference Files** - Always note which files were affected
4. **Note Concerns** - If something seems off, document it
5. **Track Time** - Approximate time spent helps planning
6. **Link Related Logs** - Reference other logs when relevant
7. **Keep Current** - Don't batch updates, log as you go

---

## 🔍 Log Maintenance

### Daily
- Review active logs for updates needed
- Ensure master_log.md is current
- Archive completed logs

### Weekly
- Review all logs for organization
- Update statistics in master_log.md
- Clean up orphaned logs

### Monthly
- Comprehensive audit of log system
- Archive old logs
- Review and improve logging practices

---

## 🔗 Related Protocols

Every protocol requires logging:
- **Analysis work** → Create analysis log
- **Research work** → Create research log
- **Generation work** → Create generation log
- **Any work** → Update appropriate log + master_log.md

---

**Remember**: Logs are the memory of the project. Without comprehensive logging, context is lost. Always log. Always update master_log.md. Always timestamp. Always document.

---

**END OF LOGGING SUB-PROTOCOL**
