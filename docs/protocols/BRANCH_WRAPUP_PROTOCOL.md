# Branch Wrapup Protocol

## Overview

This protocol defines the standard process for completing work on a version branch, documenting all accomplishments, learning, and state, then preparing for the next version. It ensures comprehensive knowledge preservation and clean transitions between development phases.

---

## Protocol Version
- **Version**: 1.0
- **Created**: 2026-01-01
- **Author**: HERMES Development Team

---

## Purpose

The Branch Wrapup Protocol serves to:
1. **Preserve Knowledge** - Document everything learned and accomplished
2. **Enable Continuity** - Create restart points for future sessions
3. **Ensure Traceability** - Maintain clear version history
4. **Facilitate Planning** - Analyze current state and plan next steps
5. **Maintain Quality** - Ensure all work is properly committed and tagged

---

## Protocol Steps

### Phase 1: Documentation (Pre-Commit)

#### Step 1.1: Create Accomplishments Document
**File Naming**: `HERMES_Quantum_ACCOMPLISHMENTS_v[VERSION]_[YYYY-MM-DD].md`

**Contents**:
- Executive summary of version goals and achievements
- Complete feature list with technical details
- Code metrics (files changed, lines added/removed)
- Screenshots or diagrams where applicable
- Performance improvements or benchmarks
- API changes or interface updates

#### Step 1.2: Create Detailed Work Log
**File Naming**: `HERMES_Quantum_WORK_LOG_v[VERSION]_[YYYY-MM-DD].md`

**Contents**:
- Chronological record of all work performed
- Each change with:
  - Date/time
  - Files modified
  - Problem addressed
  - Solution implemented
  - Code snippets (key changes only)
- Bug fixes with root cause analysis
- Refactoring decisions with rationale
- Dependencies added or updated

#### Step 1.3: Create Lessons Learned Document
**File Naming**: `HERMES_Quantum_LESSONS_LEARNED_v[VERSION]_[YYYY-MM-DD].md`

**Contents**:
- Technical discoveries and insights
- Patterns that worked well
- Anti-patterns to avoid
- Library/framework learnings
- Architecture insights
- Performance observations
- Testing discoveries
- Debugging techniques learned
- Documentation of gotchas and workarounds

#### Step 1.4: Create Analysis & Planning Document
**File Naming**: `HERMES_Quantum_ANALYSIS_AND_PLAN_v[NEXT_VERSION]_[YYYY-MM-DD].md`

**Contents**:
- Current state assessment
- Gap analysis (what's missing vs. vision)
- Technical debt inventory
- Prioritized task backlog
- Detailed plan for next version:
  - Goals and objectives
  - Feature list with complexity estimates
  - Timeline with milestones
  - Risk assessment
  - Resource requirements
- Success criteria for next version

#### Step 1.5: Create State Save Point
**File Naming**: `HERMES_Quantum_STATE_SAVEPOINT_v[VERSION]_[YYYY-MM-DD].md`

**Contents**:
- Complete project context snapshot
- Current architecture state
- File structure with key components
- Configuration state
- Environment details
- Running services and ports
- Database/storage state
- API endpoint status
- Integration points
- Known issues and workarounds
- Restart instructions
- Critical path through codebase

---

### Phase 2: Updates

#### Step 2.1: Update MASTER_PLAN.md
- Add new version to Version History
- Update current phase/status
- Revise timeline if needed
- Add newly discovered requirements
- Update risk register
- Revise success metrics if applicable

#### Step 2.2: Update EXPLORATION_LOG.md
- Add summary entry for version completion
- Document any new resources discovered
- Update technology decisions
- Note any architecture changes

#### Step 2.3: Update STATE.yaml
- Set current version
- Update phase status
- Record completion timestamp
- Update agent status if changed

---

### Phase 3: Version Control

#### Step 3.1: Pre-Commit Checklist
- [ ] All tests passing (if applicable)
- [ ] No syntax errors
- [ ] All documentation created
- [ ] MASTER_PLAN.md updated
- [ ] EXPLORATION_LOG.md updated
- [ ] STATE.yaml updated
- [ ] No sensitive data exposed
- [ ] .gitignore covers all temp files

#### Step 3.2: Stage and Commit
```bash
# Stage all changes
git add -A

# Create detailed commit message
git commit -m "v[VERSION]: [Brief description]

ACCOMPLISHMENTS:
- [Major feature 1]
- [Major feature 2]
- [Major fix 1]

DOCUMENTATION:
- Created accomplishments doc
- Created work log
- Created lessons learned
- Created v[NEXT] analysis and plan
- Created state savepoint
- Updated MASTER_PLAN
- Updated EXPLORATION_LOG

Files changed: [N] | Additions: [N] | Deletions: [N]"
```

#### Step 3.3: Push to Remote
```bash
git push origin main
```

#### Step 3.4: Create Version Tag
```bash
git tag -a v[VERSION] -m "Release v[VERSION]: [Description]"
git push origin v[VERSION]
```

---

### Phase 4: Branch Creation

#### Step 4.1: Create New Branch
```bash
git checkout -b v[NEXT_VERSION]
git push -u origin v[NEXT_VERSION]
```

#### Step 4.2: Initialize New Version
- Create initial TODO or ROADMAP for new version
- Set up any needed scaffolding
- Verify branch is active and tracked

---

### Phase 5: Verification

#### Step 5.1: Final Checks
- [ ] All commits pushed to remote
- [ ] Version tag created and pushed
- [ ] New branch created and active
- [ ] All documentation accessible
- [ ] No orphaned files or resources
- [ ] Services restarted cleanly
- [ ] State savepoint validated

#### Step 5.2: Handoff Notes
Document anything the next session needs to know:
- Urgent items
- Blocked tasks
- External dependencies
- Time-sensitive items

---

## Document Templates

### Accomplishments Template
```markdown
# HERMES_Quantum Accomplishments - v[VERSION]
**Date**: [YYYY-MM-DD]
**Duration**: [Start date] to [End date]

## Executive Summary
[2-3 sentence overview]

## Goals & Achievement Status
| Goal | Status | Notes |
|------|--------|-------|
| [Goal 1] | ✅/❌/🔄 | [Notes] |

## Feature List
### [Feature Category 1]
- **[Feature Name]**: [Description]
  - Files: [files]
  - Lines: +[added]/-[removed]

## Code Metrics
- Total files changed: [N]
- Lines added: [N]
- Lines removed: [N]
- Net change: +/-[N]

## Screenshots/Diagrams
[If applicable]
```

### State Savepoint Template
```markdown
# HERMES_Quantum State Savepoint - v[VERSION]
**Created**: [YYYY-MM-DD HH:MM]
**Git SHA**: [commit hash]

## Quick Restart
[Commands to get running]

## Project State
### Architecture
[Current architecture description]

### Key Files
| File | Purpose | State |
|------|---------|-------|
| [file] | [purpose] | [state] |

### Environment
- Python: [version]
- Key packages: [list]
- Running services: [list]

### Known Issues
1. [Issue] - [Workaround]

## Context Transfer
[Everything needed to understand current state]
```

---

## Protocol Maintenance

This protocol should be reviewed and updated:
- After each major version completion
- When new best practices emerge
- When tools or workflows change
- Quarterly at minimum

---

## Changelog

### v1.0 (2026-01-01)
- Initial protocol creation
- Defined 5-phase process
- Created document templates
- Established naming conventions
