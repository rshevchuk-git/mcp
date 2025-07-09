# AWS MCP Server


## Overview
The AWS MCP Server enables AI assistants to interact with AWS services and resources through AWS CLI commands. It provides programmatic access to manage your AWS infrastructure while maintaining proper security controls.

This server bridges the gap between AI assistants and AWS services, allowing you to create, update, and manage AWS resources across all available services. It helps with AWS CLI command selection and provides access to the latest AWS API features and services, even those released after an AI model's knowledge cutoff date.


## Prerequisites
- You must have an AWS account with credentials properly configured. Please refer to the official documentation [here ↗](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials\.html#configuring-credentials) for guidance. Note that this project follows boto3’s default credential selection order; if you have multiple AWS credentials on your machine, ensure the correct one is prioritized.
- Ensure you have Python 3.10 or newer installed. You can download it from the [official Python website](https://www.python.org/downloads/) or use a version manager such as [pyenv](https://github.com/pyenv/pyenv).
- (Optional) Install [uv](https://docs.astral.sh/uv/getting-started/installation/) for faster dependency management and improved Python environment handling.


## 📦 Installation Methods

Choose the installation method that best fits your workflow and get started with your favorite assistant with MCP support, like Q CLI, Cursor or Cline.

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/install-mcp?name=awslabs.aws-mcp-server&config=JTdCJTIyY29tbWFuZCUyMiUzQSUyMnV2eCUyMGF3c2xhYnMuYXdzLW1jcC1zZXJ2ZXIlNDBsYXRlc3QlMjIlMkMlMjJlbnYlMjIlM0ElN0IlMjJBV1NfUkVHSU9OJTIyJTNBJTIydXMtZWFzdC0xJTIyJTdEJTdE)



### 🐍 Using Python (pip)

**Step 1: Install the package**
```bash
pip install awslabs.aws-mcp-server
```

**Step 2: Configure your MCP client**
   Add the following configuration to your MCP client config file (e.g., for Amazon Q Developer CLI, edit `~/.aws/amazonq/mcp.json`):

   ```json
   {
      "mcpServers": {
        "awslabs.aws-mcp-server": {
          "command": "python",
          "args": [
            "awslabs.aws_mcp_server.server"
          ],
          "env": {
            "AWS_REGION": "us-east-1",
          },
          "disabled": false,
          "autoApprove": []
        }
      }
    }
   ```
   > **⚠️ Important:** Remove all comments from your configuration file, otherwise it will not load properly.

### ⚡ Using uv (Recommended)

**For Linux/MacOS users:**

```json
{
      "mcpServers": {
        "awslabs.aws-mcp-server": {
          "command": "uvx",
          "args": [
            "awslabs.aws-mcp-server@latest"
          ],
          "env": {
            "AWS_REGION": "us-east-1",
          },
          "disabled": false,
          "autoApprove": []
        }
      }
    }
```
> **⚠️ Important:** Remove all comments from your configuration file, otherwise it will not load properly.

**For Windows users:**

```json
   {
      "mcpServers": {
        "awslabs.aws-mcp-server": {
          "command": "uvx",
          "args": [
            "--from",
            "awslabs.aws-mcp-server@latest",
            "awslabs.aws-mcp-server.exe"
          ],
          "env": {
            "AWS_REGION": "us-east-1",
          },
          "disabled": false,
          "autoApprove": []
        }
      }
    }
```
> **⚠️ Important:** Remove all comments from your configuration file, otherwise it will not load properly.

### 🔧 Using Cloned Repository

For detailed instructions on setting up your local development environment and running the server from source, please see the [CONTRIBUTING.md](CONTRIBUTING.md) file.



## ⚙️ Configuration Options

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `AWS_REGION` | ✅ Yes | - | Default region for AWS CLI commands |
| `AWS_PROFILE` | ❌ No | `"default"` | AWS Profile for credentials to use for command executions, 'default' will be used if not specified |
| `READ_OPERATIONS_ONLY` | ❌ No | `"false"` | Primarily IAM permissions are used to control if mutating actions are allowed, so defaulting to "false" to reduce friction. We keep this as a best effort attempt to recognize and further control read-only actions. When set to "true", restricts execution to read-only operations. For a complete list of allowed operations under this flag, refer to the [Service Authorization Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html). Only operations where the **Access level** column is not `Write` will be allowed when this is set to "true". |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` | ❌ No | - | Use environment variables to configure credentials, these take precedence over `AWS_PROFILE`, read more about boto3's default order of credential sources [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials) |
| `AWS_MCP_TELEMETRY` | ❌ No | `"false"` | Allow sending additional telemetry data to AWS related to the server configuration. This includes:<br> - call_aws() tool is used with `READ_OPERATIONS_ONLY` set to true or false |


### 🚀 Quick Start

Once configured, you can ask your AI assistant questions such as:

- **"List all my EC2 instances"**
- **"Show me S3 buckets in us-west-2"**
- **"Create a new security group for web servers"** *(Admin policy only)*


## Features

- **Comprehensive AWS CLI Support**: Supports all commands available in the latest AWS CLI version, ensuring access to the most recent AWS services and features
- **Help in Command Selection**: Helps AI assistants select the most appropriate AWS CLI commands to accomplish specific tasks
- **Command Validation**: Ensures safety by validating all AWS CLI commands before execution, preventing invalid or potentially harmful operations
- **Hallucination Protection**: Mitigates the risk of model hallucination by strictly limiting execution to valid AWS CLI commands only - no arbitrary code execution is permitted
- **Security-First Design**: Built with security as a core principle, providing multiple layers of protection to safeguard your AWS infrastructure
- **Read-Only Mode**: Provides an extra layer of security that disables all mutating operations, allowing safe exploration of AWS resources


## Available MCP Tools
- `call_aws`: Executes AWS CLI commands with validation and proper error handling
- `suggest_aws_commands`: Suggests AWS CLI commands based on a natural language query. This tool helps the model generate CLI commands by providing a description and the complete set of parameters for the 3 most likely CLI commands for the given query, including the most recent AWS CLI commands - some of which may be otherwise unknown to the model (released after the model's knowledge cut-off date). This enables RAG (Retrieval-Augmented Generation) for CLI command generation via the AWS CLI command table as the knowledge source, M3 text embedding model [Chen et al., Findings of ACL 2024] for representing query and CLI documents as dense vectors, and FAISS for nearest neighbour search.


## Security Considerations
We use credentials to control which commands this MCP server can execute. This MCP server relies on IAM roles to be configured properly, in particular:
- Using credentials for an IAM role with `AdministratorAccess` policy (usually the `Admin` IAM role) permits mutating actions (i.e. creating, deleting, modifying your AWS resources) and non-mutating actions.
- Using credentials for an IAM role with `ReadOnlyAccess` policy (usually the `ReadOnly` IAM role) only allows non-mutating actions, this is sufficient if you only want to inspect resources in your account.
- If IAM roles are not available, [these alternatives](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html#cli-configure-files-examples) can also be used to configure credentials.
- To add another layer of security, users can explicitly set the environment variable `READ_OPERATIONS_ONLY` to true in their MCP config file. When set to true, we'll compare each CLI command against a list of known read-only actions, and will only execute the command if it's found in the allowed list. "Read-Only" only refers to the API classification, not the file system, that is such "read-only" actions can still write to the file system if necessary or upon user request. While this environment variable provides an additional layer of protection, IAM permissions remain the primary and most reliable security control. Users should always configure appropriate IAM roles and policies for their use case, as IAM credentials take precedence over this environment variable.

With all the security measures mentioned above, do understand that Large Langue Models (LLMs) are non-deterministic, and hallucinations can happen. It is your responsibility to use the best judgement on where to apply these tools. For example:
- A user asks the client to "Clean up my old test databases that aren't being used anymore". The LLM might assume ALL databases with "test" in the name are safe to delete, hence calling
`aws rds delete-db-instance --db-instance-identifier prod-test-analytics --region us-east-1 --skip-final-snapshot`. It fails to realize that "prod-test-analytics" was a production database used for testing analytics features. The deletion is irreversible and now the users loses all their data in that database.
- A user asks the LLM to "Download form.template from myonly s3 bucket to ~/temp/tests.txt". The LLM might create a directory `~`, under which it creates another directory `temp` to hold the `test.txt` file, it fails to understand that `~` points to the user's home directory. It was not a breaking change, but the file was created in the wrong place and the user might not be aware of it.

### File system operations
While executing commands which write files to the filesystem, please be aware that existing files can be modified, overwritten or deleted without any additional user confirmation which may lead to data loss. Users are therefore advised to be cautious when using such commands and to use their best judgement to verify the parameters the commands are being executed with.
A few examples of commands which can write to the file system include:
- `aws s3 sync`
- `aws s3 cp`
- Any AWS CLI command using the `outfile` positional argument

## License
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").


## Disclaimer
This aws-mcp package is provided "as is" without warranty of any kind, express or implied, and is intended for development, testing, and evaluation purposes only. We do not provide any guarantee on the quality, performance, or reliability of this package. LLMs are non-deterministic and they make mistakes, we advise you to always thoroughly test and follow the best practices of your organization before using these tools on customer facing accounts. Users of this package are solely responsible for implementing proper security controls and MUST use AWS Identity and Access Management (IAM) to manage access to AWS resources. You are responsible for configuring appropriate IAM policies, roles, and permissions, and any security vulnerabilities resulting from improper IAM configuration are your sole responsibility. By using this package, you acknowledge that you have read and understood this disclaimer and agree to use the package at your own risk.
