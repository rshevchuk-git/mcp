# AWS Labs aws-msk MCP Server

An AWS Labs Model Context Protocol (MCP) server for Amazon Managed Streaming for Kafka (MSK).

## Overview

The AWS MSK MCP Server provides a set of tools for interacting with Amazon MSK through the Model Context Protocol. It enables AI assistants to manage, monitor, and optimize Amazon MSK clusters by providing structured access to MSK APIs.

## Features

- **Cluster Management**: Create, describe, and update MSK clusters (both provisioned and serverless)
- **Configuration Management**: Create and manage MSK configurations
- **VPC Connection Management**: Create, describe, and manage VPC connections
- **Monitoring and Telemetry**: Access cluster metrics, logs, and operational data
- **Security Management**: Configure authentication, encryption, and access policies
- **Best Practices**: Get recommendations for cluster sizing, configuration, and performance optimization
- **Read-Only Mode**: Server runs in write mode by default, switch to read-only to protect against accidental modifications

## Tools

### Cluster Operations

- **describe_cluster_operation**: Get information about a specific cluster operation
- **get_cluster_info**: Retrieve various types of information about MSK clusters
- **get_global_info**: Get global information about MSK resources
- **create_cluster**: Create a new MSK cluster (provisioned or serverless)
- **update_broker_storage**: Update the storage size of brokers
- **update_broker_type**: Update the broker instance type
- **update_broker_count**: Update the number of brokers in a cluster
- **update_cluster_configuration**: Update the configuration of a cluster
- **update_monitoring**: Update monitoring settings
- **update_security**: Update security settings
- **reboot_broker**: Reboot brokers in a cluster

### Configuration Operations

- **get_configuration_info**: Get information about MSK configurations
- **create_configuration**: Create a new MSK configuration
- **update_configuration**: Update an existing configuration

### VPC Operations

- **describe_vpc_connection**: Get information about a VPC connection
- **create_vpc_connection**: Create a new VPC connection
- **delete_vpc_connection**: Delete a VPC connection
- **reject_client_vpc_connection**: Reject a client VPC connection request

### Security Operations

- **put_cluster_policy**: Put a resource policy on a cluster
- **associate_scram_secret**: Associate SCRAM secrets with a cluster
- **disassociate_scram_secret**: Disassociate SCRAM secrets from a cluster
- **list_tags_for_resource**: List all tags for an MSK resource
- **tag_resource**: Add tags to an MSK resource
- **untag_resource**: Remove tags from an MSK resource
- **list_customer_iam_access**: List IAM access information for a cluster

### Monitoring and Best Practices

- **get_cluster_telemetry**: Retrieve telemetry data for MSK clusters
- **get_cluster_best_practices**: Get best practices and recommendations for MSK clusters

## Usage

This MCP server can be used by AI assistants to help users manage their Amazon MSK resources. It provides structured access to MSK APIs, making it easier for AI to understand and interact with MSK clusters.

### Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/install-mcp?name=awslabs.aws-msk-mcp-server&config=JTdCJTIyY29tbWFuZCUyMiUzQSUyMnV2JTIwYXdzbGFicy5hd3MtbXNrLW1jcC1zZXJ2ZXIlMjAtLWFsbG93LXdyaXRlcyUyMiUyQyUyMmVudiUyMiUzQSU3QiUyMkZBU1RNQ1BfTE9HX0xFVkVMJTIyJTNBJTIyRVJST1IlMjIlN0QlMkMlMjJkaXNhYmxlZCUyMiUzQWZhbHNlJTJDJTIyYXV0b0FwcHJvdmUlMjIlM0ElNUIlNUQlN0Q%3D)

To use this MCP server with your MCP client, add the following configuration to your MCP client settings:

```json
"awslabs.aws-msk-mcp-server": {
    "command": "uv",
    "args": [
        "awslabs.aws-msk-mcp-server",
        "--allow-writes"
    ],
    "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
    },
    "disabled": false,
    "autoApprove": []
}

Replace `<absolute path to your server code>` with the absolute path to the server code, for example: `/Users/myuser/mcp/src/aws-msk-mcp-server/awslabs/aws_msk_mcp_server`.

Alternatively, you can use the MCP Inspector to test the server:

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory <absolute path to your server code> \
  run \
  server.py
```

### AWS Credentials

The server requires AWS credentials to access MSK resources. These can be provided through:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM roles for Amazon EC2 or ECS tasks

### Server Configuration Options

#### `--allow-writes`

By default, the MSK MCP server runs in write mode.

To disable write operations, remove the `--allow-writes` parameter to your MCP client configuration:

```json
"args": [
    "--directory",
    "<absolute path to your server code>",
    "run",
    "server.py"
    //Removed "--allow-writes"
]
```

In this mode, only read operations (tools in directories prefixed with "read_") and utility tools are available. Write operations (tools in directories prefixed with "mutate_") are disabled.

#### Region Selection

Most tools require specifying an AWS region. The server will prompt for a region if one is not provided.

## Example Use Cases

- Creating and configuring new MSK clusters
- Monitoring cluster performance and health
- Implementing best practices for MSK clusters
- Managing security and access controls
- Troubleshooting cluster issues
