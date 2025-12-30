# Tool and Reference Material Request Sub-Protocol

**Version**: 1.0.0
**Last Updated**: 2025-12-28
**Status**: Active
**Parent Protocol**: [master_protocol.md](../../master_protocol.md)

---

## Purpose

This sub-protocol governs the process of acquiring or requesting tools, MCPs, reference materials, and other resources needed for HERMES_Quantum development.

---

## 🎯 Core Principle

**Acquire or request whatever tools and reference materials you need to complete your task.**

---

## 📋 Request Procedure

### Step 1: Confirm Need

Before requesting, verify:

1. **Resource Not Already Available**
   - Check [master_protocol.md](../../master_protocol.md) indexes
   - Search workspace for existing resources
   - Verify not in standard library/tooling

2. **Need Is Justified**
   - Resource directly supports prime directive
   - No adequate alternative exists
   - Benefits outweigh costs/complexity

3. **Evaluation Complete**
   - [tool_identification_sub_protocol.md](tool_identification_sub_protocol.md) followed (for tools)
   - [reference_material_identification_sub_protocol.md](reference_material_identification_sub_protocol.md) followed (for references)
   - Multiple options compared
   - Clear recommendation made

### Step 2: Prepare Request

1. **Gather Request Information**
   ```markdown
   ## Resource Request
   
   **Type**: [Tool/MCP/Reference/SDK/Other]
   **Name**: [Resource name]
   **Purpose**: [Why it's needed]
   **Alternatives Considered**: [What else was evaluated]
   **Recommendation**: [Why this specific resource]
   **Priority**: [Critical/High/Medium/Low]
   **Urgency**: [Immediate/Soon/Can Wait]
   ```

2. **Document Acquisition Details**
   - Source (where to get it)
   - Cost (if any)
   - License requirements
   - Installation/setup process
   - Prerequisites
   - Integration requirements

3. **Assess Impact**
   - Dependencies added
   - Configuration changes needed
   - Learning curve
   - Maintenance burden
   - Security considerations

### Step 3: Submit Request

#### For Free/Open Source Resources

**Can be acquired directly if:**
- Open source with compatible license (MIT, Apache, BSD, etc.)
- No cost involved
- No security concerns
- Standard installation process

**Process:**
1. Document decision in task/research log
2. Proceed with acquisition (Step 4)
3. Update master_protocol.md after installation

#### For Paid/Proprietary Resources

**Requires user approval:**
- Any cost involved
- Proprietary licenses
- Subscription required
- Non-standard terms

**Process:**
1. Create detailed request document
2. Present to user with justification
3. Wait for approval
4. Proceed with acquisition after approval

#### For Resources Requiring Special Access

**Requires user action:**
- API keys needed
- Account creation required
- Access credentials needed
- Special permissions required

**Process:**
1. Document what's needed from user
2. Provide clear instructions
3. Wait for user to provide access
4. Proceed with configuration

### Step 4: Acquire Resource

#### For Python Packages

```bash
# Add to requirements.txt first
echo "package-name>=version" >> requirements.txt

# Install package
pip install package-name

# Verify installation
python -c "import package_name; print(package_name.__version__)"
```

#### For VS Code Extensions

```markdown
Request user install via:
1. Open Extensions view (Ctrl+Shift+X)
2. Search for "extension-name"
3. Click Install
```

Or use install_extension tool if available.

#### For MCPs

```bash
# Follow MCP-specific installation
npm install -g @modelcontextprotocol/server-name

# Or clone and setup
git clone https://github.com/org/mcp-name.git
cd mcp-name
npm install
npm run build
```

#### For Reference Materials

- Download documentation
- Save to appropriate location
- Add to version control (if license allows)
- Update reference index

### Step 5: Configure and Test

1. **Initial Configuration**
   - Add required config to project files
   - Set up environment variables (if needed)
   - Configure integration points

2. **Basic Testing**
   - Verify installation successful
   - Test basic functionality
   - Confirm integration works
   - Check for conflicts

3. **Documentation**
   - Document configuration
   - Note any quirks or gotchas
   - Create usage examples
   - Update project README if needed

### Step 6: Update Records

1. **Update master_protocol.md**
   - Add to appropriate index (Tools or References)
   - Change status from "Pending" to "Active"
   - Add documentation link
   - Note version installed

2. **Create/Update Configuration Docs**
   - Document setup process
   - Note configuration details
   - Provide usage examples
   - List troubleshooting tips

3. **Log Acquisition**
   - Create log entry with details
   - Update master_log.md
   - Note any issues encountered
   - Record lessons learned

---

## ✅ Request Checklist

Before submitting request:
- [ ] Confirmed resource not already available
- [ ] Need is justified and documented
- [ ] Evaluation protocol followed
- [ ] Alternatives compared
- [ ] Acquisition details gathered
- [ ] Impact assessed
- [ ] Request document prepared
- [ ] Priority/urgency determined

After acquisition:
- [ ] Resource acquired successfully
- [ ] Configuration completed
- [ ] Basic testing done
- [ ] Integration verified
- [ ] Documentation created
- [ ] master_protocol.md updated
- [ ] Logs updated
- [ ] Team notified (if applicable)

---

## 📊 Request Document Template

```markdown
# Resource Request: [Resource Name]

**Date**: YYYY-MM-DD HH:MM
**Requestor**: [Name/System]
**Type**: [Tool/MCP/Reference/SDK/Library/Other]
**Status**: [Pending/Approved/Acquired/Rejected]

---

## Resource Information

**Name**: [Full name]
**Version**: [Specific version if applicable]
**Source**: [URL or location]
**License**: [License type]
**Cost**: [Free/$ amount]

---

## Justification

### Problem Statement
[What problem does this solve?]

### How It Helps
[Specifically how this resource addresses the need]

### Alternatives Considered
1. **[Alternative 1]**
   - Pros: [Advantages]
   - Cons: [Disadvantages]
   - Verdict: [Why not chosen]

2. **[Alternative 2]**
   - [Same structure]

### Why This Specific Resource
[Detailed rationale for this choice]

---

## Impact Assessment

### Benefits
- [Benefit 1]: [How it helps]
- [Benefit 2]: [How it helps]

### Costs/Tradeoffs
- [Cost 1]: [Impact]
- [Cost 2]: [Impact]

### Dependencies Added
- [Dependency 1]: [Version and purpose]
- [Dependency 2]: [Version and purpose]

### Integration Effort
**Estimated Time**: [Hours/days]
**Complexity**: [Low/Medium/High]
**Changes Required**: [What needs to change]

### Security Considerations
[Any security implications]

### Maintenance Burden
[Ongoing maintenance requirements]

---

## Acquisition Plan

### Installation Steps
```bash
# Step-by-step commands
pip install resource-name
```

### Configuration Required
```python
# Configuration code
import resource_name

resource_name.configure(
    api_key="<need from user>",
    option=value
)
```

### Prerequisites
- [ ] Prerequisite 1
- [ ] Prerequisite 2

### User Action Required
[If user needs to provide credentials, create accounts, etc.]

---

## Testing Plan

### Basic Functionality Test
```python
# Test code
import resource_name

# Verify basic operation
result = resource_name.basic_operation()
assert result is not None
```

### Integration Test
[How to verify it works with existing system]

---

## Documentation Plan

### Documentation Needed
- [ ] Setup guide
- [ ] Configuration reference
- [ ] Usage examples
- [ ] Troubleshooting guide
- [ ] API reference (if applicable)

### Location
**Documentation will be added to**: [Location in project]

---

## Approval

**Priority**: [Critical/High/Medium/Low]
**Urgency**: [Immediate/Soon/Can Wait]

**Requires Approval**: [Yes/No]
**Approved By**: [Name/Date if approved]

**Decision**: [Approved/Rejected/Deferred]
**Notes**: [Any additional notes]

---

## Acquisition Log

### [YYYY-MM-DD HH:MM] - Request Created
[Details]

### [YYYY-MM-DD HH:MM] - [Status Update]
[Details]

### [YYYY-MM-DD HH:MM] - Acquired
**Version Installed**: [X.Y.Z]
**Installation Method**: [How it was installed]
**Issues Encountered**: [Any problems and solutions]
**Configuration Applied**: [Config details]
**Testing Results**: [Test outcomes]

---

## References

- Official Documentation: [URL]
- Repository: [URL]
- Evaluation Document: [Link to evaluation]
- Related Logs: [Links to related logs]
```

---

## 🚨 Critical Rules

1. **Evaluate First** - Never request without proper evaluation
2. **Document Thoroughly** - Complete request document required
3. **Get Approval When Needed** - Don't proceed without approval for paid/restricted resources
4. **Test Before Deploying** - Always test new resources
5. **Update Records** - Always update master_protocol.md and logs
6. **Consider Impact** - Assess dependencies and maintenance burden

---

## 💰 Cost Considerations

### Free Resources
- Open source tools/libraries
- Free tier APIs (with usage limits)
- Community reference materials
- Open documentation

**Can acquire directly after evaluation**

### Paid Resources
- Commercial software licenses
- Paid API tiers
- Subscription services
- Premium reference materials

**Require user approval**

### Cost-Benefit Analysis
```markdown
## Cost-Benefit Analysis

### Costs
- Direct cost: $X/month or $Y one-time
- Setup time: X hours
- Learning curve: Y hours
- Maintenance: Z hours/month

### Benefits
- Time saved: X hours/month
- Quality improvement: [Description]
- Capability added: [Description]
- Risk reduced: [Description]

### Break-even
[When do benefits outweigh costs?]

### Recommendation
[Based on analysis]
```

---

## 🔐 Security Checklist

Before acquiring any resource:

- [ ] Source is reputable and verified
- [ ] No known security vulnerabilities
- [ ] License is legitimate
- [ ] Dependencies are trustworthy
- [ ] Permissions requested are reasonable
- [ ] Data handling is appropriate
- [ ] Credential management is secure
- [ ] Updates/patches are available

---

## 🔗 Related Protocols

- **Identifying tools?** → [tool_identification_sub_protocol.md](tool_identification_sub_protocol.md)
- **Identifying references?** → [reference_material_identification_sub_protocol.md](reference_material_identification_sub_protocol.md)
- **Researching options?** → [research_sub_protocol.md](research_sub_protocol.md)
- **Logging acquisition?** → [logging_sub_protocol.md](logging_sub_protocol.md)

---

## 📈 Success Criteria

Successful acquisition when:
- Resource installed and configured correctly
- Basic functionality verified
- Integration tested
- Documentation complete
- Records updated (master_protocol.md, logs)
- No unresolved issues
- Team aware of new resource (if applicable)

---

**Remember**: Request what you need. Evaluate thoroughly. Document completely. Test before deploying. Update all records. Never proceed without proper approval for restricted resources.

---

**END OF TOOL AND REFERENCE MATERIAL REQUEST SUB-PROTOCOL**
