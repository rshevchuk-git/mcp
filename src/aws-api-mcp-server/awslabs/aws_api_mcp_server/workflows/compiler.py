# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Workflow compiler - converts YAML to immutable bytecode."""

import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from .models import WorkflowDefinition, CompiledWorkflow, WorkflowParameter, WorkflowStep, WorkflowSecurity


class WorkflowCompiler:
    """Compiles YAML workflows into immutable bytecode."""
    
    def __init__(self):
        self.compiled_workflows: Dict[str, CompiledWorkflow] = {}
    
    def compile_from_yaml(self, yaml_content: str) -> CompiledWorkflow:
        """Compile a YAML workflow definition."""
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_content)
            
            # Validate required fields
            required_fields = ['name', 'description', 'author', 'steps']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Parse parameters
            parameters = []
            for param_data in data.get('parameters', []):
                parameters.append(WorkflowParameter(**param_data))
            
            # Parse steps
            steps = []
            for step_data in data['steps']:
                steps.append(WorkflowStep(**step_data))
            
            # Parse security
            security = None
            if 'security' in data:
                security = WorkflowSecurity(**data['security'])
            
            # Create workflow definition
            definition = WorkflowDefinition(
                name=data['name'],
                version=data.get('version', '1.0'),
                description=data['description'],
                author=data['author'],
                parameters=parameters,
                steps=steps,
                security=security
            )
            
            # Compile to bytecode
            compiled = CompiledWorkflow.from_definition(definition)
            
            # Cache compiled workflow
            self.compiled_workflows[compiled.workflow_id] = compiled
            
            logger.info(f"Compiled workflow: {compiled.workflow_id}")
            return compiled
            
        except Exception as e:
            logger.error(f"Failed to compile workflow: {e}")
            raise
    
    def compile_from_file(self, file_path: Path) -> CompiledWorkflow:
        """Compile a workflow from a YAML file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            yaml_content = f.read()
        
        return self.compile_from_yaml(yaml_content)
    
    def get_compiled_workflow(self, workflow_id: str) -> CompiledWorkflow:
        """Get a compiled workflow by ID."""
        if workflow_id not in self.compiled_workflows:
            raise ValueError(f"Compiled workflow not found: {workflow_id}")
        return self.compiled_workflows[workflow_id]
    
    def validate_workflow_definition(self, definition: WorkflowDefinition) -> Dict[str, Any]:
        """Validate a workflow definition."""
        errors = []
        warnings = []
        
        # Basic validation
        if not definition.name:
            errors.append("Workflow name is required")
        
        if not definition.steps:
            errors.append("Workflow must have at least one step")
        
        # Step validation
        step_ids = set()
        for step in definition.steps:
            if step.id in step_ids:
                errors.append(f"Duplicate step ID: {step.id}")
            step_ids.add(step.id)
            
            # Validate dependencies
            if step.depends_on:
                for dep in step.depends_on:
                    if dep not in step_ids:
                        # This is a forward reference, which is okay
                        pass
        
        # Security validation
        if definition.security:
            if definition.security.max_duration > 3600:  # 1 hour
                warnings.append("Workflow duration exceeds recommended maximum (1 hour)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Global compiler instance
compiler = WorkflowCompiler()