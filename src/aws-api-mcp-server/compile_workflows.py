#!/usr/bin/env python3
"""Simple script to compile sample workflows."""

import json
import yaml
from pathlib import Path
import hashlib
from datetime import datetime


def compile_workflow(yaml_path):
    """Compile a workflow from YAML to JSON."""
    # Read YAML file
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Extract basic metadata
    name = data['name']
    version = data.get('version', '1.0')
    description = data['description']
    author = data['author']
    
    # Generate workflow ID
    workflow_id = f"{name.replace('-', '_')}_v{version.replace('.', '_')}"
    
    # Flatten parameters
    parameters = {}
    for param in data.get('parameters', []):
        parameters[param['name']] = {
            "type": param.get('type', 'string'),
            "required": param.get('required', False),
            "default": param.get('default'),
            "description": param.get('description')
        }
    
    # Compile steps to execution plan
    execution_plan = []
    for step in data['steps']:
        compiled_step = {
            "step_id": step['id'],
            "type": step['type'],
            "timeout": step.get('timeout', 300),
        }
        
        if 'intent' in step:
            compiled_step["intent"] = step['intent']
        if 'context' in step:
            compiled_step["context"] = step['context']
        if 'depends_on' in step:
            compiled_step["depends_on"] = step['depends_on']
            
        execution_plan.append(compiled_step)
    
    # Extract security info
    security_config = data.get('security', {})
    security = {
        "tier": security_config.get('tier', 'community'),
        "max_duration": security_config.get('max_duration', 600),
        "validated": True,
        "risk_score": 2.5  # Default for POC
    }
    
    # Create metadata
    metadata = {
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "created_at": datetime.utcnow().isoformat(),
        "tags": data.get('tags', [])
    }
    
    # Generate checksum
    content_for_hash = {
        "workflow_id": workflow_id,
        "metadata": metadata,
        "parameters": parameters,
        "execution_plan": execution_plan,
        "required_permissions": security_config.get('required_permissions', [])
    }
    checksum = hashlib.sha256(
        json.dumps(content_for_hash, sort_keys=True).encode()
    ).hexdigest()
    
    # Create compiled workflow
    compiled = {
        "version": "1.0",
        "format": "aws-mcp-bytecode",
        "workflow_id": workflow_id,
        "checksum": checksum,
        "metadata": metadata,
        "parameters": parameters,
        "execution_plan": execution_plan,
        "required_permissions": security_config.get('required_permissions', []),
        "security": security
    }
    
    return compiled


def main():
    """Compile all workflows in the community directory."""
    # Get paths
    base_dir = Path(__file__).parent
    community_dir = base_dir / "awslabs" / "aws_api_mcp_server" / "workflows_registry" / "community"
    compiled_dir = base_dir / "awslabs" / "aws_api_mcp_server" / "workflows_registry" / "compiled"
    
    # Create compiled directory if it doesn't exist
    compiled_dir.mkdir(parents=True, exist_ok=True)
    
    # Compile each workflow
    for yaml_file in community_dir.glob("*.yaml"):
        try:
            print(f"Compiling {yaml_file.name}...")
            compiled = compile_workflow(yaml_file)
            
            # Write compiled workflow to file
            output_file = compiled_dir / f"{compiled['workflow_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(compiled, f, indent=2, default=str)
            
            print(f"  -> Compiled to {output_file.name}")
        except Exception as e:
            print(f"Error compiling {yaml_file.name}: {e}")
    
    print("Compilation complete!")


if __name__ == "__main__":
    main()