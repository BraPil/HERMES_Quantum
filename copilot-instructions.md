# HERMES_Quantum Copilot Instructions

**Project**: HERMES_Quantum - Multi-Agent AI System for Quantum Computing Stock Analysis
**Last Updated**: 2025-12-28
**Status**: Active

---

## 🚨 CRITICAL: Read Before Every Interaction

Before responding to ANY prompt, you MUST:

1. **Consult the Master Protocol** - Review [master_protocol.md](master_protocol.md) for current directives and rules
2. **Check Applicable Sub-Protocols** - Identify and engage relevant sub-protocols based on task type
3. **Update Logs** - Ensure all work is logged per [logging_sub_protocol.md](docs/protocols/logging_sub_protocol.md)
4. **Verify Anti-Sampling Directive** - NEVER sample or skip content. Read every single word of every file.

---

## Protocol Hierarchy

```
copilot-instructions.md (YOU ARE HERE)
    ↓
master_protocol.md (Central Command & Index)
    ↓
├── Sub-Protocols
│   ├── analysis_sub_protocol.md
│   ├── research_sub_protocol.md
│   ├── generation_sub_protocol.md
│   ├── logging_sub_protocol.md
│   ├── tool_identification_sub_protocol.md
│   ├── reference_material_identification_sub_protocol.md
│   ├── tool_and_reference_material_request_sub_protocol.md
│   └── restart_sub_protocol.md
│
├── master_log.md (Log Index & Tracker)
│   └── logs/ (All operational logs)
│
└── MCP & Tools Index (in master_protocol.md)
```

---

## Prime Directive

**HERMES_Quantum Prime Directive**:

Build and maintain a comprehensive, multi-agent AI system that provides 100% complete analysis of quantum computing stocks (QBTS, IONQ, RGTI, QUBT). Every agent, data source, dependency, function, and workflow must be fully documented, mapped, and understood. All analysis must be well researched, thought out and organized. No aspect of the system architecture, data flow, or analytical capability may remain unknown or undocumented. Success criteria: Complete transparency of all system components and their relationships, enabling full system comprehension and confident expansion.

---

## Quick Reference: When to Use Each Sub-Protocol

| Task Type | Required Sub-Protocols |
|-----------|------------------------|
| Analyzing code/files | `analysis_sub_protocol.md` |
| Finding information | `research_sub_protocol.md` + `tool_identification_sub_protocol.md` |
| Creating new files/code | `generation_sub_protocol.md` + `logging_sub_protocol.md` |
| Documenting work | `logging_sub_protocol.md` |
| Need new tools/MCPs | `tool_and_reference_material_request_sub_protocol.md` |
| Context window full | `restart_sub_protocol.md` |
| Any task | `logging_sub_protocol.md` (ALWAYS) |

---

## Essential Rules (Always Active)

1. **100% Fidelity Required** - No sampling, no skipping, no assumptions
2. **Log Everything** - Every interaction must be logged with timestamp
3. **Follow Prime Directive** - All work advances the prime directive
4. **Check Master Protocol First** - Before every response
5. **Update Indexes** - Keep master_protocol.md and master_log.md current
6. **Special Characters FORBIDDEN** - No emojis or special characters in code/docs without authorization

---

## Current Project Status

**Watchlist Stocks**: QBTS, IONQ, RGTI, QUBT
**Active Agents**: 8 specialized agents (01_orchestrator through 99_models)
**Current Phase**: Initial Setup and Protocol Establishment

For detailed status, consult: [master_log.md](master_log.md)

---

## Emergency Protocols

- **Lost Context?** → Engage `restart_sub_protocol.md`
- **Unsure of Task?** → Review prime directive and relevant sub-protocols
- **Missing Tools?** → Engage `tool_and_reference_material_request_sub_protocol.md`
- **Files Too Large?** → Alert user before reading files >10,000 lines

---

**Remember**: This system exists to maintain focus, prevent context loss, and ensure comprehensive understanding of HERMES_Quantum. Every prompt response should advance the prime directive while maintaining 100% fidelity to the established protocols.
