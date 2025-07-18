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

"""Stateless workflow execution engine."""

import re
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from loguru import logger

from ..core.kb import knowledge_base
from .models import CompiledWorkflow
from .storage import get_storage


class StatelessWorkflowExecutor:
    """Executes workflow steps in a stateless manner."""
    
    def __init__(self):
        pass
    
    async def get_workflow_plan(
        self, 
        workflow_id: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get the execution plan for a workflow - pure function, no state."""
        
        # Load compiled workflow
        storage = get_storage()
        compiled_workflow = await storage.get_compiled_workflow(workflow_id)
        
        if not compiled_workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Substitute parameters in all steps
        resolved_steps = []
        for step in compiled_workflow.execution_plan:
            resolved_step = {
                "step_id": step["step_id"],
                "type": step["type"],
                "intent": self._substitute_parameters(step["intent"], parameters),
                "context": self._substitute_parameters_in_dict(step.get("context", {}), parameters),
                "timeout": step.get("timeout", 60),
                "depends_on": step.get("depends_on", [])
            }
            resolved_steps.append(resolved_step)
        
        return {
            "workflow_id": workflow_id,
            "parameters": parameters,
            "steps": resolved_steps,
            "metadata": {
                "name": compiled_workflow.metadata.name,
                "description": compiled_workflow.metadata.description,
                "author": compiled_workflow.metadata.author,
                "required_permissions": compiled_workflow.required_permissions
            }
        }
    

    
    def _substitute_parameters(self, template: str, parameters: Dict[str, Any]) -> str:
        """Substitute parameters in a template string."""
        if not isinstance(template, str):
            return template
        
        # Replace ${params.key} with actual values
        def replace_param(match):
            param_path = match.group(1)
            if param_path.startswith("params."):
                param_name = param_path[7:]  # Remove "params."
                if param_name in parameters:
                    return str(parameters[param_name])
            return match.group(0)  # Keep original if not found
        
        return re.sub(r'\$\{([^}]+)\}', replace_param, template)
    
    def _substitute_parameters_in_dict(self, template_dict: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute parameters in a dictionary."""
        result = {}
        for key, value in template_dict.items():
            if isinstance(value, str):
                result[key] = self._substitute_parameters(value, parameters)
            elif isinstance(value, dict):
                result[key] = self._substitute_parameters_in_dict(value, parameters)
            else:
                result[key] = value
        return result


# Global instance
stateless_executor = StatelessWorkflowExecutor() 