# AWS MCP Workflow System - Proof of Concept Plan

## POC Objective

Create a minimal working demonstration of the compiled workflow system that can be recorded and shared, showing:
1. Community workflow contribution (simple YAML)
2. Build-time compilation and validation
3. Runtime discovery via embeddings
4. Deterministic execution with security boundaries
5. End-to-end workflow execution

**Demo Script**: "I'll contribute a simple RDS backup workflow, compile it, discover it through natural language search, and execute it safely."

## Critical Trade-offs for POC

### What We're Building (MVP)
- **Single workflow type**: RDS backup only
- **File-based storage**: Simple directory structure, no database
- **Basic compilation**: YAML → JSON bytecode (no complex optimization)
- **Minimal security**: Input validation + permission checking (no full static analysis)
- **Community tier only**: Skip verified/enterprise tiers for now
- **Sequential execution**: No parallel steps or complex primitives
- **Local embeddings**: Reuse existing suggest_aws_commands infrastructure

### What We're Deferring (Phase 2/3)
- **Nested workflows**: Start with flat workflows only
- **Advanced primitives**: No retry, circuit breaker, complex conditions
- **Full security scanning**: Basic validation only
- **Multi-tier system**: Community tier sufficient for POC
- **Performance optimization**: Focus on correctness over speed
- **Production deployment**: Local development only

## POC Architecture

### Directory Structure
```
src/aws-api-mcp-server/
├── awslabs/aws_api_mcp_server/
│   ├── workflows/
│   │   ├── compiler.py          # YAML → Bytecode compilation
│   │   ├── executor.py          # Bytecode execution engine
│   │   ├── discovery.py         # Embeddings integration
│   │   └── security.py          # Basic validation
│   ├── workflows_registry/
│   │   ├── community/
│   │   │   └── rds-backup.yaml  # Sample workflow
│   │   └── compiled/
│   │       └── rds-backup.json  # Compiled bytecode
│   └── server.py                # Extended with new tools
```

### POC Workflow Format (Simplified)

```yaml
# workflows_registry/community/rds-backup.yaml
name: rds_backup_simple
version: "1.0"
description: "Create RDS snapshot with basic validation"
author: "poc-demo"

parameters:
  - name: instance_id
    type: string
    required: true

steps:
  - id: validate_instance
    type: command
    intent: "describe RDS instance to verify it exists"
    context:
      service: rds
      instance_id: "${params.instance_id}"
    
  - id: create_snapshot
    type: command
    intent: "create RDS snapshot for database instance"
    context:
      service: rds
      instance_id: "${params.instance_id}"
      snapshot_id: "${params.instance_id}-poc-${timestamp}"
    depends_on: [validate_instance]

security:
  required_permissions:
    - "rds:DescribeDBInstances"
    - "rds:CreateDBSnapshot"
  max_duration: 600  # 10 minutes
```

### Compiled Bytecode Format (Simplified)

```json
{
  "version": "1.0",
  "format": "aws-mcp-bytecode",
  "workflow_id": "rds_backup_simple_v1_0",
  "checksum": "sha256:abc123...",
  "metadata": {
    "name": "rds_backup_simple",
    "description": "Create RDS snapshot with basic validation",
    "author": "poc-demo",
    "tier": "community",
    "max_duration": 600,
    "created_at": "2025-01-17T10:00:00Z"
  },
  "parameters": {
    "instance_id": {"type": "string", "required": true}
  },
  "execution_plan": [
    {
      "step_id": "validate_instance",
      "type": "aws_command",
      "intent": "describe RDS instance to verify it exists",
      "context": {
        "service": "rds",
        "instance_id": "${params.instance_id}"
      },
      "next_step": "create_snapshot"
    },
    {
      "step_id": "create_snapshot", 
      "type": "aws_command",
      "intent": "create RDS snapshot for database instance",
      "context": {
        "service": "rds",
        "instance_id": "${params.instance_id}",
        "snapshot_id": "${params.instance_id}-poc-${timestamp}"
      },
      "depends_on": ["validate_instance"]
    }
  ],
  "required_permissions": [
    "rds:DescribeDBInstances",
    "rds:CreateDBSnapshot"
  ],
  "security": {
    "tier": "community",
    "validated": true,
    "risk_score": 2.5
  }
}
```

## POC Implementation Tasks

### Phase 1: Core POC (2-3 weeks)

#### ✅ Task 1: Workflow Compiler (Week 1) - COMPLETED
**Goal**: YAML → JSON compilation with basic validation

**Deliverables**:
- ✅ `workflows/compiler.py` - Basic YAML parser and validator
- ✅ JSON bytecode generation
- ✅ Checksum calculation for immutability
- ✅ Basic schema validation

**Acceptance Criteria**:
- ✅ Can compile sample RDS backup workflow
- ✅ Generates valid JSON bytecode
- ✅ Validates required fields and types
- ✅ Calculates SHA256 checksum

#### ✅ Task 2: Execution Engine (Week 1-2) - COMPLETED
**Goal**: Execute compiled workflows deterministically

**Deliverables**:
- ✅ `workflows/executor.py` - Bytecode execution engine
- ✅ Integration with existing `suggest_aws_commands`
- ✅ Integration with existing `call_aws`
- ✅ Basic parameter substitution

**Acceptance Criteria**:
- ✅ Can execute compiled RDS backup workflow
- ✅ Uses suggest_aws_commands for intent → CLI command
- ✅ Uses call_aws for command execution
- ✅ Handles parameter substitution correctly

#### ✅ Task 3: MCP Tool Integration (Week 2) - COMPLETED
**Goal**: Add workflow tools to aws-api-mcp-server

**Deliverables**:
- ✅ `suggest_workflows` tool implementation
- ✅ `execute_workflow` tool implementation
- ✅ Integration with existing embeddings infrastructure

**Acceptance Criteria**:
- ✅ `suggest_workflows("backup my RDS database")` returns relevant workflows
- ✅ `execute_workflow("rds_backup_simple", {"instance_id": "test-db"})` executes successfully
- ✅ Tools integrate seamlessly with existing MCP server

#### ✅ Task 4: Discovery System (Week 2-3) - COMPLETED
**Goal**: Embeddings-based workflow discovery

**Deliverables**:
- ✅ `workflows/discovery.py` - Embeddings integration
- ✅ Workflow metadata indexing
- ✅ Search and ranking functionality

**Acceptance Criteria**:
- ✅ Workflows indexed in embeddings system
- ✅ Natural language queries return relevant workflows
- ✅ Results ranked by relevance and user permissions

#### ⚠️ Task 5: Basic Security (Week 3) - PARTIALLY COMPLETED
**Goal**: Essential security boundaries

**Deliverables**:
- ⚠️ `workflows/security.py` - Permission validation (basic validation in executor)
- ✅ Input sanitization
- ✅ Execution timeout enforcement

**Acceptance Criteria**:
- ⚠️ Validates user has required AWS permissions (basic parameter validation only)
- ✅ Sanitizes workflow parameters
- ✅ Enforces maximum execution duration
- ⚠️ Prevents basic injection attempts (parameter substitution sanitization)

### Phase 1 Demo Script

**Setup** (30 seconds):
```bash
# Start aws-api-mcp-server with workflow extensions
cd src/aws-api-mcp-server
python -m awslabs.aws_api_mcp_server.server
```

**Demo Flow** (3-4 minutes):

1. **Show Workflow Contribution** (30 seconds):
   ```bash
   # Display the simple YAML workflow
   cat workflows_registry/community/rds-backup.yaml
   ```

2. **Compile Workflow** (30 seconds):
   ```bash
   # Compile workflow to bytecode
   python -m awslabs.aws_api_mcp_server.workflows.compiler \
     workflows_registry/community/rds-backup.yaml
   
   # Show compiled bytecode
   cat workflows_registry/compiled/rds-backup.json
   ```

3. **Discover Workflow** (60 seconds):
   ```python
   # Through MCP client
   suggest_workflows("I need to backup my RDS database")
   # Returns: rds_backup_simple workflow with description
   ```

4. **Execute Workflow** (90 seconds):
   ```python
   # Through MCP client
   execute_workflow("rds_backup_simple", {
     "instance_id": "demo-database"
   })
   # Shows step-by-step execution with AWS CLI commands
   ```

5. **Show Security** (30 seconds):
   ```python
   # Attempt to execute without permissions
   execute_workflow("rds_backup_simple", {
     "instance_id": "../../etc/passwd"  # Injection attempt
   })
   # Shows security validation and rejection
   ```

## Phase 2/3 Expansion Plan

### Phase 2: Hardening (Weeks 4-8)
- **Advanced Security**: Static analysis, vulnerability scanning
- **Nested Workflows**: Composition and dependency resolution
- **Multi-tier System**: Verified and Enterprise tiers
- **Advanced Primitives**: Retry, timeout, conditional execution
- **Performance Optimization**: Caching, parallel execution

### Phase 3: Production Ready (Weeks 9-16)
- **Community Platform**: Contribution and review system
- **Full Test Suite**: Unit, integration, and security tests
- **Monitoring and Observability**: Execution tracking and alerting
- **Documentation**: Complete user and developer guides
- **Production Deployment**: Scalable infrastructure

## Key POC Decisions & Rationale

### 1. Single Workflow Type (RDS Backup)
**Decision**: Focus on one concrete use case
**Rationale**: Proves the concept without complexity, easy to understand and demo
**Reversibility**: High - architecture supports multiple workflow types

### 2. File-Based Storage
**Decision**: Use filesystem instead of database
**Rationale**: Eliminates infrastructure dependencies, faster development
**Reversibility**: High - storage layer is abstracted with repository pattern
**Implementation**: Use clean storage interface from day one

### 3. Basic Compilation Only
**Decision**: Simple YAML → JSON transformation
**Rationale**: Proves immutability concept without complex optimization
**Reversibility**: High - can enhance compiler without breaking format
**Critical**: Version bytecode format immediately (v1.0) to avoid one-way door

### 4. Community Tier Only
**Decision**: Skip multi-tier security model implementation
**Rationale**: Reduces complexity while proving core security concepts
**Reversibility**: High - tier system is additive
**Enhancement**: Stub out enterprise/premium tiers with "upgrade required" messages

### 5. Sequential Execution
**Decision**: No parallel or complex flow control
**Rationale**: Simpler execution engine, easier to debug
**Reversibility**: Medium - may require execution engine refactoring

## Success Criteria for POC

### Technical Success
- [ ] Workflow compiles from YAML to immutable bytecode
- [ ] Discovery works through natural language queries
- [ ] Execution is deterministic and secure
- [ ] Integration with existing aws-api-mcp-server is seamless
- [ ] Demo runs end-to-end without errors

### Business Success
- [ ] Demo is compelling and easy to understand
- [ ] Architecture clearly supports future expansion
- [ ] Security model is credible and demonstrable
- [ ] Community contribution model is evident
- [ ] Video recording is professional and shareable

## Critical POC Improvements (Based on Expert Review)

### 1. Architecture Safeguards
**Bytecode Format Versioning**: Include version and format fields from day one to avoid one-way doors
**Clean Interfaces**: Use repository pattern even for file storage to enable easy swapping later
**Extensible Security**: Stub out enterprise tiers with "upgrade required" messages

### 2. Demo Enhancement Strategy
**Pre-seed Discovery**: Create 5-10 diverse workflows to ensure search results are compelling
**Security Theater**: Make security validation visually obvious (green checkmarks, "Validated" badges)
**Complex Example**: Include one multi-step workflow (RDS backup → S3 → SNS) to show power

### 3. Technical Debt Prevention
```python
# Use clean abstractions from day one
class WorkflowEngine:
    def __init__(self, storage: WorkflowStorage, security: SecurityValidator):
        pass

class FileWorkflowStorage(WorkflowStorage):
    # POC implementation - easily replaceable
    pass
```

### 4. Demo Narrative Structure (4 minutes)
1. **Problem** (30s): "Finding and trusting community AWS workflows is hard"
2. **Solution** (30s): Show the marketplace concept
3. **Contribution** (60s): YAML → compiled → published
4. **Discovery** (60s): Natural language search finding perfect workflow
5. **Execution** (60s): Run it, show security gates, show success
6. **Vision** (30s): Tease enterprise features

## Risk Mitigation

### Technical Risks
- **Integration Complexity**: Start with minimal changes to existing server
- **Embeddings Performance**: Reuse existing infrastructure, pre-seed with quality workflows
- **Security Gaps**: Focus on essential boundaries, defer advanced features
- **Discovery Failure**: Biggest demo risk - ensure search results are compelling

### Timeline Risks
- **Scope Creep**: Strict adherence to POC-only features
- **AWS Dependencies**: Use mock/test AWS resources where possible
- **Demo Failures**: Extensive testing of demo script, have fallback options
- **Critical Path**: Workflow execution engine (5-6 days), Security validation (2-3 days), Discovery system (2-3 days)

### Quality Risks
- **Technical Debt**: Document all shortcuts and temporary solutions
- **Architecture Drift**: Regular validation against full specification
- **Security Shortcuts**: Clearly document what's deferred vs. implemented
- **One-Way Doors**: Version everything from start (bytecode format, API, workflow schema)

## Next Steps

1. **Validate POC Plan**: Review with stakeholders and technical team
2. **Set Up Development Environment**: Prepare aws-api-mcp-server for extension
3. **Create Sample Workflow**: Write and test RDS backup YAML
4. **Begin Implementation**: Start with Task 1 (Workflow Compiler)
5. **Iterative Testing**: Test each component as it's built
6. **Demo Preparation**: Practice demo script and prepare recording setup