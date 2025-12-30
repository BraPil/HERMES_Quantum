# Research Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs all research activities within HERMES_Quantum. It ensures comprehensive information gathering to support well researched, thought out and organized decision-making.

---

## 🎯 Core Principle

**Identify tools and reference materials needed, ask for any that are missing, and then use those to comprehensively research in 100% full detail and granularity.**

---

## 📋 Research Procedure

### Step 1: Define Research Scope

1. **Identify Research Question**
   - What exactly needs to be researched?
   - Why is this information needed?
   - How will it be used?

2. **Define Success Criteria**
   - What level of detail is required?
   - What sources are authoritative?
   - When is research "complete"?

3. **Identify Known Resources**
   - Available documentation
   - Existing code/files
   - Previous research
   - Team knowledge

### Step 2: Identify Required Tools & References

1. **Assess Available Tools**
   - Review [master_protocol.md](../../master_protocol.md) MCP & Tool Index
   - Identify tools currently available
   - Note gaps in tooling

2. **Identify Needed Tools**
   - What tools would make research more effective?
   - Are there specialized MCPs needed?
   - What APIs or integrations are required?
   - Engage [tool_identification_sub_protocol.md](tool_identification_sub_protocol.md)

3. **Assess Available References**
   - Review [master_protocol.md](../../master_protocol.md) Reference Material Index
   - Check workspace documentation
   - Identify existing reference materials

4. **Identify Needed References**
   - What documentation is missing?
   - What SDKs or libraries are needed?
   - What external resources would help?
   - Engage [reference_material_identification_sub_protocol.md](reference_material_identification_sub_protocol.md)

### Step 3: Request Missing Resources

**If any tools or references are missing:**
1. Engage [tool_and_reference_material_request_sub_protocol.md](tool_and_reference_material_request_sub_protocol.md)
2. Document request in research log
3. Wait for approval/acquisition
4. Update [master_protocol.md](../../master_protocol.md) indexes when received

**DO NOT proceed with inadequate resources** - always request what you need.

### Step 4: Conduct Comprehensive Research

1. **Execute Research Plan**
   - Use ALL available tools
   - Consult ALL relevant references
   - Search workspace files thoroughly
   - Check external authoritative sources

2. **Maintain 100% Fidelity**
   - Read complete documents (no sampling)
   - Verify all claims with sources
   - Cross-reference information
   - Note conflicting information

3. **Document As You Go**
   - Take detailed notes
   - Record all sources
   - Note uncertainty or gaps
   - Track time spent on each area

### Step 5: Synthesize Findings

1. **Organize Information**
   - Group related findings
   - Identify patterns and themes
   - Resolve conflicts in sources
   - Note confidence levels

2. **Analyze Completeness**
   - Have all research questions been answered?
   - Are there remaining gaps?
   - Is additional research needed?
   - Are findings sufficient for decision-making?

3. **Prepare Summary**
   - Key findings
   - Source citations
   - Confidence assessments
   - Recommendations

### Step 6: Document Research

1. **Create Research Log**
   - Follow naming: `Research_[Topic]_[YYYY-MM-DD]_[HHMM].md`
   - Save to: `logs/research/`
   - Update [master_log.md](../../master_log.md)

2. **Include All Required Elements** (see template below)

---

## ✅ Research Checklist

Before considering research complete, verify:

- [ ] Research question clearly defined
- [ ] All needed tools have been identified and acquired
- [ ] All needed references have been identified and acquired
- [ ] All available sources have been consulted
- [ ] All information has been verified
- [ ] Conflicting information has been resolved or noted
- [ ] Sources have been properly cited
- [ ] Findings are comprehensive and detailed
- [ ] Research log has been created
- [ ] master_log.md has been updated
- [ ] Findings are well researched, thought out and organized

---

## 🔍 Research Types

### Technical Research
**Purpose**: Understanding technical implementations, APIs, frameworks
**Sources**: Documentation, code examples, SDK references, technical blogs
**Deliverables**: Technical summary, implementation recommendations, code examples

### Market Research
**Purpose**: Understanding market conditions, trends, competitor analysis
**Sources**: Financial data, news sources, analyst reports, social media
**Deliverables**: Market summary, trend analysis, competitive landscape

### Academic Research
**Purpose**: Understanding theoretical foundations, algorithms, methodologies
**Sources**: Papers, textbooks, academic journals, research repositories
**Deliverables**: Literature review, methodology recommendations, citations

### Operational Research
**Purpose**: Understanding best practices, workflows, procedures
**Sources**: Industry standards, case studies, documentation, expert opinions
**Deliverables**: Best practices summary, workflow recommendations, process maps

---

## 📊 Research Output Template

```markdown
# Research: [Topic]

**Date**: YYYY-MM-DD HH:MM
**Researcher**: [Name/System]
**Research Question**: [Clear statement of what was researched]
**Status**: [Complete/In Progress/Blocked]

## Executive Summary
[High-level summary of findings - 2-3 paragraphs]

## Research Scope
**Goals**: [What we aimed to discover]
**Success Criteria**: [How we measure completeness]
**Limitations**: [Any scope limitations or constraints]

## Tools & Resources Used
### Tools
- Tool 1: [Purpose and how it was used]
- Tool 2: [Purpose and how it was used]

### Reference Materials
- Reference 1: [Type and relevance]
- Reference 2: [Type and relevance]

## Methodology
[How research was conducted - step by step]

## Key Findings

### Finding 1: [Title]
**Source**: [Citation]
**Confidence**: [High/Medium/Low]
**Details**: [Comprehensive explanation]
**Implications**: [What this means for the project]

### Finding 2: [Title]
[Same structure as above]

## Analysis & Synthesis
[How findings relate to each other, patterns identified, insights gained]

## Gaps & Uncertainties
1. [Gap description and why it exists]
2. [Uncertainty and potential resolution]

## Recommendations
1. [Recommendation with supporting evidence]
2. [Recommendation with supporting evidence]

## Next Steps
- [ ] Action item based on findings
- [ ] Additional research needed
- [ ] Implementation steps

## Source Bibliography
1. [Complete source citation 1]
2. [Complete source citation 2]

## Appendices
[Additional details, data tables, code examples, etc.]
```

---

## 🚨 Critical Rules

1. **Request What You Need** - Never proceed without necessary tools/references
2. **Cite All Sources** - Every finding must be traceable to its source
3. **Verify Everything** - Don't trust single sources, cross-reference
4. **Note Uncertainty** - If something is unclear or uncertain, say so
5. **Comprehensive Detail** - Research must be thorough and complete
6. **No Sampling** - Read complete sources, not summaries or excerpts

---

## 🔗 Related Protocols

- **Need to identify tools?** → [tool_identification_sub_protocol.md](tool_identification_sub_protocol.md)
- **Need to identify references?** → [reference_material_identification_sub_protocol.md](reference_material_identification_sub_protocol.md)
- **Need to request resources?** → [tool_and_reference_material_request_sub_protocol.md](tool_and_reference_material_request_sub_protocol.md)
- **Analyzing findings?** → [analysis_sub_protocol.md](analysis_sub_protocol.md)
- **Logging research?** → [logging_sub_protocol.md](logging_sub_protocol.md)

---

## 📈 Research Quality Indicators

Good research exhibits:
- Multiple authoritative sources cited
- Clear methodology documented
- Findings verified and cross-referenced
- Uncertainty explicitly noted
- Comprehensive coverage of topic
- Actionable recommendations
- Proper documentation and logging

---

**Remember**: Quality research is thorough, well-sourced, and comprehensive. Never rush research. Always request needed resources. Always verify findings. Always document sources.

---

**END OF RESEARCH SUB-PROTOCOL**
