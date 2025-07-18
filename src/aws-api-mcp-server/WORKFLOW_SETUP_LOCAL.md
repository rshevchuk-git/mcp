# Running AWS MCP Workflow System Locally

This guide provides step-by-step instructions for setting up and running the AWS MCP Workflow System from source code.

## Prerequisites

- Python 3.10 or newer
- AWS credentials configured
- Git repository cloned locally
- Working directory for AWS operations

## Setup Instructions

### 1. Install Dependencies

First, make sure you're in the aws-api-mcp-server directory:

```bash
cd src/aws-api-mcp-server
```

Install dependencies using uv:

```bash
uv sync
```

Or using pip:

```bash
pip install -e .
```

### 2. Create Working Directory

Create a directory for AWS operations:

```bash
mkdir -p /tmp/aws-workflow-demo
```

### 3. Configure MCP Client

Add the following configuration to your MCP client config file. For example, for Kiro, edit `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "aws-api-workflow-poc": {
      "command": "python",
      "args": [
        "-m",
        "awslabs.aws_api_mcp_server.server"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_API_MCP_WORKING_DIR": "/tmp/aws-workflow-demo",
        "PYTHONPATH": "${workspaceFolder}/src/aws-api-mcp-server",
        "FASTMCP_LOG_LEVEL": "DEBUG"
      },
      "cwd": "${workspaceFolder}/src/aws-api-mcp-server",
      "disabled": false,
      "autoApprove": ["suggest_workflows", "execute_workflow"]
    }
  }
}
```

**Note**: Replace `/tmp/aws-workflow-demo` with your preferred working directory path.

### 4. Compile Sample Workflows

Run the workflow compilation script to ensure all sample workflows are compiled:

```bash
cd src/aws-api-mcp-server
python compile_workflows.py
```

This will compile the YAML workflows in `workflows_registry/community/` to JSON bytecode in `workflows_registry/compiled/`.

## Testing the Workflow System

### 1. Start the MCP Server

The MCP server will start automatically when you connect your MCP client.

### 2. Test Workflow Discovery

In your MCP client, run:

```python
suggest_workflows("backup my RDS database")
```

Expected output:
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

### 3. Test Workflow Execution

In your MCP client, run:

```python
execute_workflow("rds_backup_simple_v1_0", {
  "instance_id": "my-test-database"
})
```

This will execute the RDS backup workflow, which will:
1. Validate that the RDS instance exists
2. Create a snapshot of the RDS instance

## Troubleshooting

### Workflow Storage Not Initialized

If you see an error like "Workflow storage not initialized", check:
- The server is started properly
- The `workflows_registry` directory exists
- You've run `compile_workflows.py`

### No Workflows Found to Index

If you see "No workflows found to index", run:
```bash
python compile_workflows.py
```

### Embeddings Issues

If workflow discovery isn't working properly:
- Check that the knowledge base is initialized
- Verify that the embeddings are generated
- Look for errors in the server logs

### Execution Errors

If workflow execution fails:
- Check that the AWS credentials are properly configured
- Verify that the required permissions are available
- Check the parameters passed to the workflow

## Logs and Debugging

Server logs are stored in:
- Linux: `/tmp/aws-api-mcp/aws-api-mcp-server.log`
- macOS: `/var/folders/.../T/aws-api-mcp/aws-api-mcp-server.log`
- Windows: `%TEMP%\aws-api-mcp\aws-api-mcp-server.log`

Set `FASTMCP_LOG_LEVEL=DEBUG` for more detailed logs.

## Adding New Workflows

To add a new workflow:

1. Create a YAML file in `workflows_registry/community/`
2. Run `python compile_workflows.py` to compile it
3. Restart the server to index the new workflow

## Demo Script

For a complete demo, follow this sequence:

1. **Show Discovery**: `suggest_workflows("backup my RDS database")`
2. **Show Execution**: `execute_workflow("rds_backup_simple_v1_0", {"instance_id": "demo-db"})`
3. **Show Security**: Try invalid parameters to demonstrate validation
4. **Show Compilation**: Display YAML → JSON compilation process