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

"""Workflow execution engine - deterministic bytecode execution."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from loguru import logger

from ..core.kb import knowledge_base
from .models import CompiledWorkflow, WorkflowExecution
from .storage import get_storage


class WorkflowExecutor:
    """Executes compiled workflows deterministically."""
    
    def __init__(self):
        # Tool functions that can be called during execution
        self.tool_functions: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool function for workflow execution."""
        self.tool_functions[name] = func
        logger.debug(f"Registered tool: {name}")
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        parameters: Dict[str, Any],
        execution_mode: str = "step_by_step"
    ) -> WorkflowExecution:
        """Execute a compiled workflow."""
        try:
            # Get compiled workflow
            storage = get_storage()
            workflow = await storage.get_compiled_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Validate parameters
            self._validate_parameters(workflow, parameters)
            
            # Create execution context
            execution = WorkflowExecution(
                execution_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                parameters=parameters,
                status="running"
            )
            
            # Save initial execution state
            await storage.save_execution(execution)
            
            logger.info(f"Starting workflow execution: {execution.execution_id}")
            
            # Execute steps
            try:
                await self._execute_steps(workflow, execution)
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                logger.info(f"Workflow execution completed: {execution.execution_id}")
                
            except Exception as e:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                logger.error(f"Workflow execution failed: {execution.execution_id} - {e}")
                raise
            
            finally:
                # Save final execution state
                await storage.save_execution(execution)
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise
    
    def _validate_parameters(self, workflow: CompiledWorkflow, parameters: Dict[str, Any]) -> None:
        """Validate workflow parameters."""
        # Check required parameters
        for param_name, param_config in workflow.parameters.items():
            if param_config.get("required", False) and param_name not in parameters:
                raise ValueError(f"Required parameter missing: {param_name}")
        
        # Basic type validation (simplified for POC)
        for param_name, value in parameters.items():
            if param_name in workflow.parameters:
                expected_type = workflow.parameters[param_name].get("type", "string")
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Parameter {param_name} must be a string")
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ValueError(f"Parameter {param_name} must be an integer")
    
    async def _execute_steps(self, workflow: CompiledWorkflow, execution: WorkflowExecution) -> None:
        """Execute workflow steps in order."""
        for step in workflow.execution_plan:
            step_id = step["step_id"]
            execution.current_step = step_id
            
            logger.info(f"Executing step: {step_id}")
            
            try:
                # Execute the step based on its type
                if step["type"] == "command":
                    result = await self._execute_command_step(step, execution)
                elif step["type"] == "wait":
                    result = await self._execute_wait_step(step, execution)
                else:
                    raise ValueError(f"Unknown step type: {step['type']}")
                
                # Store step result
                execution.step_results[step_id] = result
                logger.debug(f"Step {step_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Step {step_id} failed: {e}")
                raise
    
    async def _execute_command_step(self, step: Dict[str, Any], execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a command step using suggest_aws_commands + call_aws."""
        intent = step.get("intent")
        context = step.get("context", {})
        
        if not intent:
            raise ValueError(f"Command step {step['step_id']} missing intent")
        
        # Substitute parameters in intent and context
        resolved_intent = self._substitute_parameters(intent, execution.parameters)
        resolved_context = self._substitute_parameters_in_dict(context, execution.parameters)
        
        # Build query for suggest_aws_commands
        query = self._build_command_query(resolved_intent, resolved_context)
        
        logger.debug(f"Command query: {query}")
        
        # Get command suggestions
        suggestions = knowledge_base.get_suggestions(query)
        
        if not suggestions.get('suggestions'):
            raise RuntimeError(f"No command suggestions found for: {query}")
        
        # Use the highest confidence suggestion
        best_suggestion = suggestions['suggestions'][0]
        command = best_suggestion['command']
        
        logger.info(f"Executing AWS command: {command}")
        
        # Execute the command using call_aws tool
        if 'call_aws' not in self.tool_functions:
            raise RuntimeError("call_aws tool not registered")
        
        call_aws_func = self.tool_functions['call_aws']
        result = await call_aws_func(command)
        
        return {
            "command": command,
            "suggestion_confidence": best_suggestion.get('similarity', 0.0),
            "result": result
        }
    
    async def _execute_wait_step(self, step: Dict[str, Any], execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a wait step (simplified for POC)."""
        timeout = step.get("timeout", 30)
        condition = step.get("condition", "")
        
        logger.info(f"Waiting for condition: {condition} (timeout: {timeout}s)")
        
        # For POC, just wait for the timeout period
        # In a real implementation, this would poll for the actual condition
        await asyncio.sleep(min(timeout, 10))  # Cap at 10 seconds for demo
        
        return {
            "condition": condition,
            "waited_seconds": min(timeout, 10),
            "status": "completed"
        }
    
    def _substitute_parameters(self, text: str, parameters: Dict[str, Any]) -> str:
        """Substitute parameters in text using ${param.name} syntax."""
        result = text
        for param_name, param_value in parameters.items():
            placeholder = f"${{params.{param_name}}}"
            result = result.replace(placeholder, str(param_value))
        return result
    
    def _substitute_parameters_in_dict(self, data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute parameters in a dictionary."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._substitute_parameters(value, parameters)
            elif isinstance(value, dict):
                result[key] = self._substitute_parameters_in_dict(value, parameters)
            else:
                result[key] = value
        return result
    
    def _build_command_query(self, intent: str, context: Dict[str, Any]) -> str:
        """Build a query for suggest_aws_commands."""
        query_parts = [intent]
        
        # Add context information
        if "service" in context:
            query_parts.append(f"using {context['service']} service")
        
        # Add other context as natural language
        for key, value in context.items():
            if key != "service" and isinstance(value, str):
                query_parts.append(f"{key} {value}")
        
        return " ".join(query_parts)


# Global executor instance
executor = WorkflowExecutor()