#!/usr/bin/env python3
"""Test script for workflow execution."""

import asyncio
import json
from pathlib import Path


async def test_workflow_discovery():
    """Test workflow discovery."""
    print("\n=== Testing Workflow Discovery ===")
    
    # Simulate suggest_workflows tool
    query = "backup my RDS database"
    print(f"Query: '{query}'")
    
    # Load compiled workflows
    compiled_dir = Path(__file__).parent / "awslabs" / "aws_api_mcp_server" / "workflows_registry" / "compiled"
    workflows = []
    
    for json_file in compiled_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            workflow = json.load(f)
            workflows.append(workflow)
    
    # Simple keyword matching for POC test
    matches = []
    for workflow in workflows:
        score = 0
        text = f"{workflow['metadata']['name']} {workflow['metadata']['description']}"
        
        # Check for keyword matches
        keywords = query.lower().split()
        for keyword in keywords:
            if keyword in text.lower():
                score += 1
        
        if score > 0:
            matches.append({
                "workflow_id": workflow["workflow_id"],
                "name": workflow["metadata"]["name"],
                "description": workflow["metadata"]["description"],
                "author": workflow["metadata"]["author"],
                "similarity": score / len(keywords),
                "required_permissions": workflow["required_permissions"]
            })
    
    # Sort by similarity
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Print results
    if matches:
        print(f"Found {len(matches)} matching workflows:")
        for i, match in enumerate(matches):
            print(f"{i+1}. {match['name']} - {match['description']} (similarity: {match['similarity']:.2f})")
    else:
        print("No matching workflows found.")
    
    return matches


async def test_workflow_execution(workflow_id, parameters):
    """Test workflow execution."""
    print(f"\n=== Testing Workflow Execution: {workflow_id} ===")
    print(f"Parameters: {parameters}")
    
    # Load the compiled workflow
    compiled_dir = Path(__file__).parent / "awslabs" / "aws_api_mcp_server" / "workflows_registry" / "compiled"
    workflow_file = compiled_dir / f"{workflow_id}.json"
    
    if not workflow_file.exists():
        print(f"Error: Workflow {workflow_id} not found.")
        return None
    
    with open(workflow_file, 'r') as f:
        workflow = json.load(f)
    
    # Validate parameters
    for param_name, param_config in workflow["parameters"].items():
        if param_config.get("required", False) and param_name not in parameters:
            print(f"Error: Required parameter '{param_name}' is missing.")
            return None
    
    # Simulate execution
    print(f"Executing workflow: {workflow['metadata']['name']}")
    print(f"Description: {workflow['metadata']['description']}")
    print(f"Author: {workflow['metadata']['author']}")
    print(f"Required permissions: {', '.join(workflow['required_permissions'])}")
    
    # Execute steps
    results = {}
    for step in workflow["execution_plan"]:
        step_id = step["step_id"]
        step_type = step["type"]
        
        print(f"\nExecuting step: {step_id} ({step_type})")
        
        if "intent" in step:
            print(f"Intent: {step['intent']}")
        
        if step_type == "command":
            # Simulate AWS CLI command execution
            if "intent" in step:
                # Generate a mock AWS CLI command based on intent
                service = step.get("context", {}).get("service", "")
                command = f"aws {service} "
                
                if "describe" in step["intent"].lower():
                    command += "describe-"
                elif "create" in step["intent"].lower():
                    command += "create-"
                elif "list" in step["intent"].lower():
                    command += "list-"
                
                if service == "rds" and "instance" in step["intent"].lower():
                    command += f"db-instances --db-instance-identifier {parameters.get('instance_id', 'example-db')}"
                elif service == "s3" and "bucket" in step["intent"].lower():
                    command += f"bucket --bucket {parameters.get('bucket_name', 'example-bucket')}"
                elif service == "ec2" and "instance" in step["intent"].lower():
                    command += "instances"
                
                print(f"Generated command: {command}")
                
                # Simulate command execution
                print("Command executed successfully.")
                results[step_id] = {
                    "command": command,
                    "status": "success",
                    "result": {"Message": "Simulated successful execution"}
                }
        
        elif step_type == "wait":
            # Simulate wait step
            print(f"Waiting for condition...")
            await asyncio.sleep(1)  # Just a short delay for demo
            print("Wait completed.")
            results[step_id] = {
                "status": "success",
                "waited_seconds": 1
            }
    
    print("\nWorkflow execution completed successfully!")
    return {
        "execution_id": "sim-12345",
        "workflow_id": workflow_id,
        "status": "completed",
        "parameters": parameters,
        "step_results": results
    }


async def main():
    """Run the test script."""
    print("=== AWS MCP Workflow System POC Test ===")
    
    # Test workflow discovery
    matches = await test_workflow_discovery()
    
    if matches:
        # Test workflow execution with the top match
        top_match = matches[0]
        
        # Set up test parameters
        if "rds" in top_match["workflow_id"]:
            parameters = {"instance_id": "test-db-instance"}
        elif "s3" in top_match["workflow_id"]:
            parameters = {"bucket_name": "test-bucket"}
        else:
            parameters = {}
        
        # Execute the workflow
        await test_workflow_execution(top_match["workflow_id"], parameters)


if __name__ == "__main__":
    asyncio.run(main())