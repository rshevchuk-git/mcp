# AWS MCP Workflow System - Setup & Testing Guide

## Overview

The AWS MCP Workflow System extends the aws-api-mcp-server with community-contributed workflows that can be discovered through natural language and executed deterministically. This guide covers setup, testing, and usage.

## 🚀 Quick Start

### Prerequisites
- AWS API MCP Server installed and configured (see main README.md)
- Python 3.10+ with required dependencies
- AWS credentials configured
- Working directory set via `AWS_API_MCP_WORKING_DIR`

### 1. Verify Installation

The workflow system is automatically included with the aws-api-mcp-server. Verify it's working:

```bash
# Start the server
cd src/aws-api-mcp-server
python -m awslabs.aws_api_mcp_server.server
```

### 2. Available Workflow Tools

The server now includes two additional MCP tools:

- **`suggest_workflows`** - Discover workflows using natural language
- **`execute_workflow`** - Execute compiled workflows with parameters

### 3. Sample Workflows

Pre-compiled sample workflows are included:

- **RDS Backup** (`rds_backup_simple_v1_0`) - Create RDS database snapshots
- **S3 Lifecycle** (`s3_lifecycle_policy_v1_0`) - Configure S3 lifecycle policies

## 🔍 Testing the Workflow System

### Test 1: Workflow Discovery

Test natural language workflow discovery:

```python
# Through your MCP client
suggest_workflows("I need to backup my RDS database")
```

**Expected Result:**
```json
[
  {
    "workflow_id": "rds_backup_simple_v1_0",
    "name": "rds-backup",
    "description": "Create RDS snapshot with basic validation",
    "author": "aws-mcp-poc",
    "similarity": 0.85,
    "required_permissions": [
      "rds:DescribeDBInstances",
      "rds:CreateDBSnapshot"
    ],
    "parameters": [
      {
        "name": "instance_id",
        "type": "string",
        "required": true,
        "description": "RDS instance identifier"
      }
    ]
  }
]
```

### Test 2: Workflow Execution

Execute a workflow with parameters:

```python
# Through your MCP client
execute_workflow("rds_backup_simple_v1_0", {
  "instance_id": "my-test-database"
})
```

**Expected Result:**
```json
{
  "execution_id": "uuid-here",
  "workflow_id": "rds_backup_simple_v1_0",
  "status": "completed",
  "parameters": {
    "instance_id": "my-test-database"
  },
  "step_results": {
    "validate_instance": {
      "command": "aws rds describe-db-instances --db-instance-identifier my-test-database",
      "suggestion_confidence": 0.95,
      "result": { ... }
    },
    "create_snapshot": {
      "command": "aws rds create-db-snapshot --db-instance-identifier my-test-database --db-snapshot-identifier my-test-database-poc-20250118",
      "suggestion_confidence": 0.92,
      "result": { ... }
    }
  },
  "started_at": "2025-01-18T10:00:00Z",
  "completed_at": "2025-01-18T10:02:30Z"
}
```

### Test 3: Error Handling

Test parameter validation:

```python
# Missing required parameter
execute_workflow("rds_backup_simple_v1_0", {})
```

**Expected Result:**
```json
{
  "detail": "Required parameter missing: instance_id"
}
```

## 📁 Directory Structure

```
src/aws-api-mcp-server/awslabs/aws_api_mcp_server/
├── workflows/                    # Core workflow system
│   ├── models.py                # Data models and validation
│   ├── compiler.py              # YAML → JSON compilation
│   ├── executor.py              # Workflow execution engine
│   ├── discovery.py             # Embeddings-based search
│   └── storage.py               # File-based storage
├── workflows_registry/          # Workflow storage
│   ├── community/               # Source YAML workflows
│   │   ├── rds-backup.yaml
│   │   └── s3-lifecycle.yaml
│   ├── compiled/                # Compiled JSON bytecode
│   │   ├── rds_backup_simple_v1_0.json
│   │   └── s3_lifecycle_policy_v1_0.json
│   └── executions/              # Runtime execution state
└── server.py                    # Extended MCP server
```

## 🔧 Advanced Testing

### Manual Workflow Compilation

Compile new workflows manually:

```bash
cd src/aws-api-mcp-server
python compile_workflows.py
```

### Check Compiled Workflows

View compiled bytecode:

```bash
cat awslabs/aws_api_mcp_server/workflows_registry/compiled/rds_backup_simple_v1_0.json
```

### Workflow Indexing

Workflows are automatically indexed for discovery when the server starts. To manually refresh:

```python
from awslabs.aws_api_mcp_server.workflows.discovery import discovery
await discovery.refresh_index()
```

## 🛡️ Security Features

### Parameter Validation
- Required parameter checking
- Type validation (string, integer, etc.)
- Input sanitization to prevent injection

### Execution Boundaries
- Maximum execution duration (10 minutes default)
- Step-by-step logging and monitoring
- Deterministic execution from immutable bytecode

### Permission Checking
- Workflows declare required AWS permissions
- Basic parameter sanitization
- Timeout enforcement

## 🐛 Troubleshooting

### Common Issues

**1. "Workflow storage not initialized"**
```
Solution: Ensure the server is started properly and workflows_registry directory exists
```

**2. "No workflows found to index"**
```
Solution: Run compile_workflows.py to compile YAML workflows to JSON bytecode
```

**3. "No command suggestions found"**
```
Solution: Check that the knowledge base is properly initialized and embeddings are available
```

**4. "call_aws tool not registered"**
```
Solution: Ensure the server.py properly registers the call_aws tool with the executor
```

### Debug Mode

Enable debug logging:

```bash
export FASTMCP_LOG_LEVEL=DEBUG
python -m awslabs.aws_api_mcp_server.server
```

### Workflow Execution Logs

Check execution logs in:
```
awslabs/aws_api_mcp_server/workflows_registry/executions/
```

## 📊 Testing Checklist

- [ ] Server starts without errors
- [ ] `suggest_workflows` returns relevant results
- [ ] `execute_workflow` completes successfully
- [ ] Parameter validation works correctly
- [ ] Error handling is appropriate
- [ ] Workflow compilation works
- [ ] Discovery indexing functions
- [ ] Security boundaries are enforced

## 🎯 Demo Script

For a complete demo, follow this sequence:

1. **Show Discovery**: `suggest_workflows("backup my RDS database")`
2. **Show Execution**: `execute_workflow("rds_backup_simple_v1_0", {"instance_id": "demo-db"})`
3. **Show Security**: Try invalid parameters to demonstrate validation
4. **Show Compilation**: Display YAML → JSON compilation process

## 🔄 Embeddings Generation

**Automatic Generation**: Workflow embeddings are generated automatically when:
- The server starts up
- New workflows are compiled
- Discovery indexing is triggered

**Manual Generation**: To manually refresh embeddings:
```python
from awslabs.aws_api_mcp_server.workflows.discovery import discovery
await discovery.index_workflows()
```

The system reuses the existing embeddings infrastructure from the aws-api-mcp-server, so no additional setup is required.