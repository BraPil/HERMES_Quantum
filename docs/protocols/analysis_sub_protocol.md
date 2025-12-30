# Analysis Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs all analysis activities within HERMES_Quantum. It ensures that every analysis is comprehensive, thorough, and maintains 100% fidelity to the prime directive.

---

## 🎯 Core Principle

**Analyze every single word of every single result thoroughly and in full 100% comprehensiveness.**

NO sampling. NO skipping. NO assumptions.

---

## 📋 Analysis Procedure

### Step 1: Pre-Analysis Preparation

1. **Review Anti-Sampling Directive** from [master_protocol.md](../../master_protocol.md)
2. **Identify Analysis Scope**
   - What specifically needs to be analyzed?
   - What files/components are involved?
   - What relationships must be understood?
3. **Gather All Required Materials**
   - Collect ALL relevant files
   - Identify ALL dependencies
   - Note file sizes (alert if >10,000 lines)

### Step 2: Comprehensive Reading

1. **Read EVERY File Completely**
   - Start from line 1
   - Read to final line
   - No sampling or skipping
   - Take notes as you read

2. **Document While Reading**
   - Key functions and their purposes
   - Dependencies and imports
   - Data flows and transformations
   - Potential issues or concerns

### Step 3: Relationship Mapping

1. **Identify All Dependencies**
   - Direct dependencies
   - Indirect dependencies
   - Circular dependencies
   - External dependencies

2. **Map Data Flows**
   - Input sources
   - Transformation steps
   - Output destinations
   - Side effects

3. **Document Relationships**
   - Component interactions
   - Agent communications
   - Tool integrations
   - External API calls

### Step 4: Deep Analysis

1. **Functional Analysis**
   - What does each component do?
   - How does it accomplish its purpose?
   - What are the success criteria?
   - What are potential failure modes?

2. **Architectural Analysis**
   - How do components fit together?
   - What patterns are being used?
   - Are there architectural concerns?
   - What are scaling considerations?

3. **Quality Analysis**
   - Code quality and maintainability
   - Documentation completeness
   - Test coverage
   - Performance considerations

### Step 5: Findings Documentation

1. **Create Analysis Log**
   - Follow naming convention: `Analysis_[Description]_[YYYY-MM-DD]_[HHMM].md`
   - Save to: `logs/analysis/`
   - Update [master_log.md](../../master_log.md)

2. **Document Everything Discovered**
   - All components analyzed
   - All relationships identified
   - All dependencies mapped
   - All concerns noted
   - All recommendations made

3. **Create Visual Maps** (if applicable)
   - Dependency diagrams
   - Data flow diagrams
   - Architecture diagrams
   - Component relationship maps

---

## ✅ Analysis Checklist

Before considering analysis complete, verify:

- [ ] ALL relevant files have been read completely (no sampling)
- [ ] ALL dependencies have been identified and documented
- [ ] ALL relationships have been mapped
- [ ] ALL data flows have been traced
- [ ] ALL functions/methods have been documented
- [ ] ALL concerns have been noted
- [ ] ALL recommendations have been made
- [ ] Analysis log has been created and saved
- [ ] master_log.md has been updated
- [ ] Findings are well researched, thought out and organized

---

## 🎯 Analysis Types

### Code Analysis
**Focus**: Understanding code structure, logic, and quality
**Deliverables**: 
- Function/method documentation
- Dependency map
- Code quality assessment
- Refactoring recommendations

### System Analysis
**Focus**: Understanding overall system architecture
**Deliverables**:
- Architecture diagram
- Component relationship map
- Integration points documentation
- Scaling recommendations

### Data Analysis
**Focus**: Understanding data structures and flows
**Deliverables**:
- Data model documentation
- Data flow diagrams
- Data quality assessment
- Data pipeline documentation

### Agent Analysis
**Focus**: Understanding agent behavior and interactions
**Deliverables**:
- Agent capability documentation
- Inter-agent communication map
- Agent workflow documentation
- Agent optimization recommendations

---

## 🚨 Critical Rules

1. **100% Completeness Required** - No analysis is complete until ALL aspects are understood
2. **No Assumptions** - Everything must be verified by reading actual code/documentation
3. **Document Everything** - If you discovered it, document it
4. **Verify Understanding** - Can you explain how every piece works and why?
5. **Follow Up Questions** - If anything is unclear, engage research_sub_protocol.md

---

## 📊 Analysis Output Template

```markdown
# Analysis: [Component Name]

**Date**: YYYY-MM-DD HH:MM
**Analyst**: [Name/System]
**Scope**: [What was analyzed]
**Status**: [Complete/In Progress/Blocked]

## Summary
[High-level summary of findings]

## Components Analyzed
- Component 1: [Purpose and findings]
- Component 2: [Purpose and findings]
...

## Dependencies Identified
- Dependency 1: [Type and relationship]
- Dependency 2: [Type and relationship]
...

## Data Flows Mapped
1. [Flow description]
2. [Flow description]
...

## Concerns Identified
1. [Concern description and severity]
2. [Concern description and severity]
...

## Recommendations
1. [Recommendation with rationale]
2. [Recommendation with rationale]
...

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
...

## References
- [File 1](path/to/file1)
- [File 2](path/to/file2)
...
```

---

## 🔗 Related Protocols

- **Research Needed?** → [research_sub_protocol.md](research_sub_protocol.md)
- **Logging Results** → [logging_sub_protocol.md](logging_sub_protocol.md)
- **Need Tools?** → [tool_identification_sub_protocol.md](tool_identification_sub_protocol.md)

---

## 📈 Success Metrics

Analysis is successful when:
- 100% of scope has been analyzed
- All relationships are documented
- All dependencies are mapped
- All concerns are identified
- User/system can fully understand analyzed components
- Documentation is comprehensive and clear

---

**Remember**: Thorough analysis is the foundation of the prime directive. Never rush analysis. Never sample. Never assume. Always verify. Always document.

---

**END OF ANALYSIS SUB-PROTOCOL**
