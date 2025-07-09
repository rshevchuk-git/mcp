## Contributing

### Local Development

To make changes to this MCP locally and run it:

1. Clone this repository:
```bash
git clone https://github.com/awslabs/mcp.git
cd mcp/src/aws-mcp-server
```

2. Install gh from the [installation guide](https://cli.github.com/)
  - Log in by `gh auth login`
  - Verify log-in status by `gh auth status`. ---> You should see "Logged in to github.com account ***"

3. Install dependencies:
```bash
uv sync
```

4. Configure AWS credentials and environment variables:
   - Ensure you have AWS credentials configured as you did during installation, read more [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)


5. Run the server:
Add the following code to your MCP client configuration (e.g., for Amazon Q Developer CLI, edit `~/.aws/amazonq/mcp.json`). Configuration is similar to "Installation" in README.md.

```
{
  "mcpServers": {
    "awslabs.aws-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "<your_working_directory>/mcp/src/aws-mcp-server",
        "run",
        "awslabs.aws-mcp-server"
      ],
      "env": {
        "AWS_REGION": "us-east-1", // Required. Set your default region to be assumed for CLI commands, if not specified explicitly in the request.
        "AWS_MCP_WORKING_DIR": "/path/to/working/directory", // Required. Working directory for resolving relative paths in commands like 'aws s3 cp'.
        "AWS_MCP_PROFILE_NAME": "<your_profile_name>" // Optional. AWS Profile for credentials. Read more under "Environment variables" in README.md.
        "READ_OPERATIONS_ONLY": "false", // Optional. Only allows read-only operations as per ReadOnlyAccess policy. Default is "false"
        "AWS_MCP_TELEMETRY": "false" // Optional. Allow the storage of telemetry data. Default is "false". Read more under "Environment variables" in README.md.
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```


&nbsp;

### Publishing

To publish local changes for review:

1. Create a new local branch and make your changes
```bash
git checkout -b <your_branch_name> # use proper prefix
```

2. Make sure you current directory is at `<your_working_directory>/mcp/src/aws-mcp-server`:
```bash
uv run --frozen pyright
```

3. Run pre-commit checks:
```bash
cd ../..
pre-commit run --all-files
```

4. Commit and push to remote, open a PR on Github

&nbsp;
