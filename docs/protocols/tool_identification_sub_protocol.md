# Tool Identification Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol guides the identification of tools, MCPs (Model Context Protocols), and utilities needed to accomplish tasks within HERMES_Quantum.

---

## 🎯 Core Principle

**When called upon, look for the most effective tools and MCPs to help you accomplish your task.**

---

## 📋 Tool Identification Procedure

### Step 1: Define Tool Requirements

1. **Identify the Task**
   - What exactly needs to be accomplished?
   - What are the inputs and outputs?
   - What are the constraints?

2. **Specify Tool Criteria**
   - What capabilities are required?
   - What integrations are needed?
   - What performance requirements exist?
   - What compatibility requirements exist?

3. **Review Existing Tools**
   - Check [master_protocol.md](../../master_protocol.md) MCP & Tool Index
   - Can existing tools be used or adapted?
   - Are there similar tools already in use?

### Step 2: Research Available Tools

1. **Search VS Code Marketplace**
   - Extensions for specific functionality
   - Language-specific tools
   - Integration tools

2. **Search MCP Registry**
   - Model Context Protocol servers
   - Pre-built integrations
   - Community MCPs

3. **Search Package Registries**
   - PyPI for Python packages
   - npm for Node.js tools
   - System package managers (apt, brew, etc.)

4. **Search Developer Resources**
   - GitHub repositories
   - Official documentation
   - Developer communities

### Step 3: Evaluate Tool Options

For each potential tool, assess:

1. **Functionality**
   - Does it meet requirements?
   - What are its capabilities?
   - What are its limitations?

2. **Quality**
   - Is it actively maintained?
   - What is its reputation/rating?
   - Are there known issues?

3. **Compatibility**
   - Works with Python 3.9+?
   - Compatible with existing stack?
   - Dependencies acceptable?

4. **Documentation**
   - Well documented?
   - Examples available?
   - Support available?

5. **License**
   - Compatible with project license (MIT)?
   - Commercial use allowed?
   - Attribution requirements?

6. **Performance**
   - Resource requirements acceptable?
   - Speed adequate for use case?
   - Scalability considerations?

### Step 4: Make Recommendation

1. **Document Findings**
   ```markdown
   ## Tool Evaluation: [Tool Name]
   
   **Purpose**: [What it's for]
   **Source**: [Where to get it]
   **License**: [License type]
   
   ### Pros
   - [Advantage 1]
   - [Advantage 2]
   
   ### Cons
   - [Limitation 1]
   - [Limitation 2]
   
   ### Verdict
   [Recommended/Not Recommended] because [reason]
   ```

2. **Compare Alternatives**
   - Create comparison table if multiple options
   - Highlight key differences
   - Make clear recommendation

3. **Prepare Request**
   - If tool is needed, prepare for request sub-protocol
   - Document installation/setup requirements
   - Note any prerequisites

### Step 5: Log Identification Work

1. **Create Log Entry**
   - Add to research log or task log
   - Document tools evaluated
   - Record decision rationale

2. **Update Master Protocol**
   - If tool recommended, note in master_protocol.md
   - Track as "Pending" until acquired

---

## ✅ Tool Identification Checklist

- [ ] Task requirements clearly defined
- [ ] Tool criteria specified
- [ ] Existing tools reviewed
- [ ] Multiple sources searched
- [ ] At least 3 options evaluated (if available)
- [ ] Functionality verified
- [ ] Compatibility verified
- [ ] Documentation quality checked
- [ ] License compatibility verified
- [ ] Performance considerations assessed
- [ ] Clear recommendation made
- [ ] Findings documented
- [ ] Log updated

---

## 🛠️ Tool Categories for HERMES_Quantum

### Data Acquisition Tools
**Purpose**: Getting stock data, news, social media
**Examples**:
- Financial data APIs (yfinance, alpha_vantage)
- News APIs (NewsAPI, GDELT)
- Social media APIs (Twitter, Reddit)

### Analysis Tools
**Purpose**: Processing and analyzing data
**Examples**:
- pandas, numpy for data manipulation
- scikit-learn for ML
- statsmodels for statistical analysis

### Visualization Tools
**Purpose**: Creating charts and dashboards
**Examples**:
- matplotlib, plotly, seaborn
- Dash for dashboards
- Grafana for monitoring

### NLP/Sentiment Tools
**Purpose**: Text analysis and sentiment
**Examples**:
- transformers (BERT, etc.)
- NLTK, spaCy
- TextBlob for simple sentiment

### Database Tools
**Purpose**: Data storage and retrieval
**Examples**:
- SQLite, PostgreSQL
- Redis for caching
- InfluxDB for time series

### Workflow Tools
**Purpose**: Orchestration and automation
**Examples**:
- Apache Airflow
- Prefect
- Cron jobs

### Testing Tools
**Purpose**: Quality assurance
**Examples**:
- pytest for testing
- black for formatting
- mypy for type checking

### Development Tools
**Purpose**: Development workflow
**Examples**:
- VS Code extensions
- Git tools
- Debugging tools

---

## 📊 Tool Evaluation Template

```markdown
# Tool Evaluation: [Tool Name]

**Date**: YYYY-MM-DD HH:MM
**Evaluator**: [Name/System]
**Purpose**: [Why this tool is being evaluated]
**Status**: [Recommended/Not Recommended/Needs More Research]

---

## Tool Information

**Name**: [Full tool name]
**Version**: [Current version]
**Source**: [URL or package registry]
**License**: [License type]
**Maintainer**: [Organization or individual]
**Last Updated**: [Date of last update]

---

## Requirements Match

| Requirement | Met? | Notes |
|-------------|------|-------|
| [Requirement 1] | ✓/✗ | [Details] |
| [Requirement 2] | ✓/✗ | [Details] |
| [Requirement 3] | ✓/✗ | [Details] |

---

## Capabilities

### Core Features
- [Feature 1]: [Description]
- [Feature 2]: [Description]

### Additional Features
- [Feature 1]: [Description]
- [Feature 2]: [Description]

### Limitations
- [Limitation 1]: [Impact]
- [Limitation 2]: [Impact]

---

## Technical Assessment

### Compatibility
- **Python Version**: [Compatible versions]
- **OS Support**: [Supported operating systems]
- **Dependencies**: [Key dependencies]
- **Conflicts**: [Any known conflicts]

### Performance
- **Speed**: [Performance characteristics]
- **Resource Usage**: [Memory, CPU requirements]
- **Scalability**: [How well it scales]

### Quality
- **Maintenance**: [Activity level]
- **Community**: [Size and engagement]
- **Issues**: [Open issue count and severity]
- **Documentation**: [Quality rating]

---

## Integration Considerations

### Installation
```bash
# Installation commands
pip install [tool-name]
```

### Configuration
[What configuration is needed]

### Code Integration
```python
# Example usage
import tool_name

# Basic usage example
```

---

## Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| [Tool A] | [Advantages] | [Disadvantages] | [Better/Worse] |
| [Tool B] | [Advantages] | [Disadvantages] | [Better/Worse] |

---

## Recommendation

**Status**: [Highly Recommended / Recommended / Not Recommended / Needs More Research]

**Rationale**:
[Detailed explanation of recommendation]

**Conditions** (if any):
- [Condition 1]
- [Condition 2]

**Next Steps**:
- [ ] Request approval for acquisition
- [ ] Prepare installation documentation
- [ ] Plan integration approach

---

## References

- Official Documentation: [URL]
- GitHub Repository: [URL]
- Package Registry: [URL]
- Related Articles: [URLs]
```

---

## 🚨 Critical Rules

1. **Thorough Evaluation** - Don't recommend first tool found
2. **Compare Options** - Always evaluate multiple alternatives
3. **Check Compatibility** - Verify it works with our stack
4. **Verify Maintenance** - Avoid abandoned projects
5. **Consider Alternatives** - Is there a better option?
6. **Document Everything** - Record evaluation process and findings

---

## 🔗 Related Protocols

- **Need reference materials?** → [reference_material_identification_sub_protocol.md](reference_material_identification_sub_protocol.md)
- **Ready to request tool?** → [tool_and_reference_material_request_sub_protocol.md](tool_and_reference_material_request_sub_protocol.md)
- **Researching options?** → [research_sub_protocol.md](research_sub_protocol.md)

---

## 📈 Quality Indicators

Good tool identification includes:
- Multiple options evaluated
- Clear comparison of alternatives
- Verified compatibility
- Documented pros and cons
- Clear recommendation with rationale
- Installation and integration plan
- Proper logging of decision

---

**Remember**: The right tool makes the job easier. The wrong tool creates technical debt. Always evaluate thoroughly. Always compare alternatives. Always document your findings.

---

**END OF TOOL IDENTIFICATION SUB-PROTOCOL**
