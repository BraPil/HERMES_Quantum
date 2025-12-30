# HERMES_Quantum Master Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Project**: HERMES_Quantum - Multi-Agent AI System for Quantum Computing Stock Analysis

---

## 🎯 Prime Directive

**HERMES_Quantum Prime Directive**:

Build and maintain a comprehensive, multi-agent AI system that provides 100% complete analysis of quantum computing stocks (QBTS, IONQ, RGTI, QUBT). Every agent, data source, dependency, function, and workflow must be fully documented, mapped, and understood. All analysis must be well researched, thought out and organized. No aspect of the system architecture, data flow, or analytical capability may remain unknown or undocumented. Success criteria: Complete transparency of all system components and their relationships, enabling full system comprehension and confident expansion.

---

## 🚨 Anti-Sampling Directive

### CRITICAL RULE: 100% Fidelity Required

**This directive is MANDATORY and NON-NEGOTIABLE.**

You are **STRICTLY PROHIBITED** from:
- Reading only the first 100 lines of a file
- Sampling portions of a file
- Generating in your memory what you think the rest of a file contains
- Skipping sections of code or documentation
- Making assumptions about file contents without reading them completely

**REQUIRED BEHAVIOR:**

1. **Read Every Single Word** - No matter the length, read the ENTIRE file
2. **Files Over 10,000 Lines** - Alert the user and get explicit authorization before proceeding
3. **100% Fidelity Requirement** - We need complete understanding of:
   - 100% of relationships
   - 100% of dependencies  
   - 100% of capabilities
   - 100% of functionality

**Rationale**: Incomplete reading leads to missed dependencies, incorrect assumptions, and system failures. HERMES_Quantum requires complete comprehension to achieve the prime directive.

---

## 📋 Sub-Protocol Index

### Active Sub-Protocols

| Sub-Protocol | File | Purpose | Last Updated | Status |
|--------------|------|---------|--------------|--------|
| Analysis | [analysis_sub_protocol.md](docs/protocols/analysis_sub_protocol.md) | Comprehensive code/file analysis | 2025-12-28 | Active |
| Research | [research_sub_protocol.md](docs/protocols/research_sub_protocol.md) | Information gathering & investigation | 2025-12-28 | Active |
| Generation | [generation_sub_protocol.md](docs/protocols/generation_sub_protocol.md) | Creating code, docs, and files | 2025-12-28 | Active |
| Logging | [logging_sub_protocol.md](docs/protocols/logging_sub_protocol.md) | Tracking all work and decisions | 2025-12-28 | Active |
| Tool Identification | [tool_identification_sub_protocol.md](docs/protocols/tool_identification_sub_protocol.md) | Finding appropriate tools/MCPs | 2025-12-28 | Active |
| Reference Material | [reference_material_identification_sub_protocol.md](docs/protocols/reference_material_identification_sub_protocol.md) | Locating SDK's, docs, references | 2025-12-28 | Active |
| Tool/Reference Request | [tool_and_reference_material_request_sub_protocol.md](docs/protocols/tool_and_reference_material_request_sub_protocol.md) | Acquiring needed resources | 2025-12-28 | Active |
| Restart | [restart_sub_protocol.md](docs/protocols/restart_sub_protocol.md) | Context window refresh procedure | 2025-12-28 | Active |

### How to Use Sub-Protocols

1. **Identify Task Type** - Determine which sub-protocol(s) apply
2. **Read Relevant Sub-Protocol(s)** - Fully read applicable protocols (remember: no sampling!)
3. **Follow Protocol Steps** - Execute according to sub-protocol requirements
4. **Log Results** - Always engage logging_sub_protocol.md
5. **Update Indexes** - Update this file and master_log.md as needed

---

## 📊 Master Log Reference

**Location**: [master_log.md](master_log.md)

The master log serves as the central index for all operational logs. It tracks:
- All task logs and their status
- Issue-specific logs
- Session logs
- Analysis logs
- Research logs
- Generation logs

**Update Frequency**: After every significant action or at minimum once per prompt response.

---

## 🛠️ MCP & Tool Index

### Currently Integrated Tools

| Tool/MCP | Purpose | Status | Documentation |
|----------|---------|--------|---------------|
| VS Code Copilot | AI pair programming | Active | Built-in |
| Terminal | Command execution | Active | Built-in |
| File System | File operations | Active | Built-in |

### Needed Tools/MCPs (To Be Acquired)

| Tool/MCP | Purpose | Priority | Status |
|----------|---------|----------|--------|
| Financial Data API | Stock data ingestion | High | Pending |
| News API | News aggregation | High | Pending |
| Social Media API | Sentiment analysis | Medium | Pending |
| ML Framework | Model training/inference | High | Pending |

**Process for Adding Tools**: Follow [tool_and_reference_material_request_sub_protocol.md](docs/protocols/tool_and_reference_material_request_sub_protocol.md)

---

## 📚 Reference Material Index

### Available Reference Materials

| Reference | Type | Location | Purpose |
|-----------|------|----------|---------|
| README.md | Documentation | `/workspaces/HERMES_Quantum/README.md` | Project overview |
| MASTER_PLAN.md | Documentation | `/workspaces/HERMES_Quantum/docs/MASTER_PLAN.md` | Strategic roadmap |
| pyproject.toml | Configuration | `/workspaces/HERMES_Quantum/pyproject.toml` | Project config |
| watchlist.yaml | Configuration | `/workspaces/HERMES_Quantum/config/watchlist.yaml` | Stock watchlist |

### Needed Reference Materials

| Reference | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| Quantum Computing Industry Reports | Context for analysis | High | Pending |
| Financial Analysis SDK Docs | Implementation guidance | High | Pending |
| Multi-Agent System Patterns | Architecture reference | Medium | Pending |

---

## 🔄 Standard Operating Procedures

### For Every Prompt Interaction

1. **Read copilot-instructions.md** - Understand current context
2. **Consult This Master Protocol** - Verify directives and rules
3. **Engage Applicable Sub-Protocols** - Follow relevant procedures
4. **Execute Task** - Maintain 100% fidelity
5. **Log Everything** - Document work per logging_sub_protocol.md
6. **Update Indexes** - Keep master_protocol.md and master_log.md current

### Task-Specific Procedures

**Analysis Tasks**:
1. Engage analysis_sub_protocol.md
2. Read ALL relevant files completely (anti-sampling directive)
3. Document findings per logging_sub_protocol.md
4. Update master_log.md

**Research Tasks**:
1. Engage research_sub_protocol.md
2. Identify needed tools/references
3. Execute comprehensive research
4. Document findings and sources
5. Update master_log.md

**Generation Tasks**:
1. Engage generation_sub_protocol.md
2. Follow coding standards (NO special characters/emojis)
3. Document code comprehensively
4. Test generated code
5. Update master_log.md

**Restart Required**:
1. Engage restart_sub_protocol.md
2. Review entire chat history
3. Ensure all logs are current
4. Generate comprehensive restart prompt
5. Update master_log.md before restart

---

## 🎨 Code & Documentation Standards

### MANDATORY Standards

1. **No Special Characters** - STRICTLY FORBIDDEN unless expressly necessary with authorization
2. **No Emojis** - NEVER use emojis in code or documentation without explicit authorization
3. **Complete Documentation** - Every function, class, module must be documented
4. **Type Hints** - Use Python type hints consistently
5. **Descriptive Names** - Clear, self-documenting variable and function names

### Documentation Requirements

- **Files**: Header comment with purpose, dependencies, and usage
- **Classes**: Docstring with purpose, attributes, methods overview
- **Functions**: Docstring with parameters, returns, raises, examples
- **Modules**: README.md with overview, setup, usage

---

## 📈 Progress Tracking

### Current System Comprehension

| Component | Understanding | Documentation | Status |
|-----------|---------------|---------------|--------|
| Project Structure | 80% | Complete | In Progress |
| Agent System | 40% | Partial | Needs Mapping |
| Data Ingestion | 20% | Minimal | Needs Analysis |
| Execution Flow | 30% | Minimal | Needs Analysis |
| Dependencies | 90% | Complete | Good |

**Goal**: Achieve 100% understanding and documentation across all components per prime directive.

---

## 🚦 Status Indicators

- **Active** - Currently operational and maintained
- **Pending** - Planned but not yet implemented
- **In Progress** - Currently being worked on
- **Complete** - Finished and documented
- **Deprecated** - No longer in use

---

## 📞 Emergency Contacts & Escalation

**Context Loss**: Engage restart_sub_protocol.md immediately
**Unknown Dependencies**: Stop, engage research_sub_protocol.md, document findings
**Missing Tools**: Engage tool_and_reference_material_request_sub_protocol.md
**Directive Conflict**: Escalate to user immediately

---

## 🔄 Version History

| Version | Date | Changes | Updated By |
|---------|------|---------|------------|
| 1.0.0 | 2025-12-28 | Initial protocol establishment | Setup Process |

---

**END OF MASTER PROTOCOL**

*This protocol is the central command center for all HERMES_Quantum operations. All sub-protocols, logs, and operations reference back to this document.*
