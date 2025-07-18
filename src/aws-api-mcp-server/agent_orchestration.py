"""
Agent orchestration functions for stateless workflow execution.
These functions help the host agent (LLM) orchestrate workflow execution
without maintaining state in the workflow engine.
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def find_next_executable_step(remaining_steps: List[Dict], completed_steps: Dict[str, Any]) -> Optional[Dict]:
    """Find the next step where all dependencies are satisfied."""
    for step in remaining_steps:
        dependencies = step.get("depends_on", [])
        if all(dep in completed_steps for dep in dependencies):
            return step
    return None


def build_command_with_parameters(suggestion: Dict, context: Dict[str, Any]) -> str:
    """Build AWS CLI command with parameters from context."""
    base_command = suggestion.get("command", "")
    param_metadata = suggestion.get("parameters", {})
    
    # Extract parameter names from metadata
    command_parts = [base_command]
    
    for param_name, param_info in param_metadata.items():
        if param_name in context:
            # Add parameter to command
            param_value = context[param_name]
            command_parts.append(f"--{param_name}")
            command_parts.append(str(param_value))
    
    return " ".join(command_parts)


def extract_parameter_names(param_metadata: Dict[str, str]) -> List[str]:
    """Extract parameter names from AWS CLI parameter metadata."""
    param_names = []
    
    for param_name, param_info in param_metadata.items():
        # Parameter info is like "``--bucket`` (string) The bucket name..."
        # We want to extract "bucket" from "--bucket"
        if param_name.startswith("--"):
            clean_name = param_name[2:]  # Remove "--"
            param_names.append(clean_name)
        else:
            param_names.append(param_name)
    
    return param_names


async def generate_command_for_step(
    step: Dict, 
    completed_steps: Dict[str, Any],
    suggest_aws_commands_func,
    context: Dict[str, Any]
) -> str:
    """Generate AWS CLI command for a workflow step."""
    
    intent = step["intent"]
    step_context = step.get("context", {})
    
    # Build query for suggest_aws_commands
    query_parts = [intent]
    
    # Add service information
    if "service" in step_context:
        query_parts.append(f"using {step_context['service']} service")
    
    # Add context parameters as hints
    for key, value in step_context.items():
        if key != "service":
            query_parts.append(f"with {key} {value}")
    
    query = " ".join(query_parts)
    
    # Get suggestions from AWS CLI knowledge base
    suggestions = await suggest_aws_commands_func(query)
    
    if not suggestions.get("suggestions"):
        raise ValueError(f"No command suggestions found for: {query}")
    
    # Use the best suggestion
    best_suggestion = suggestions["suggestions"][0]
    
    # Build command with parameters
    command = build_command_with_parameters(best_suggestion, step_context)
    
    return command


async def execute_workflow_stateless(
    workflow_id: str,
    parameters: Dict[str, Any],
    get_workflow_plan_func,
    call_aws_func,
    suggest_aws_commands_func
) -> Dict[str, Any]:
    """Execute a workflow in a stateless manner using agent orchestration."""
    
    # 1. Get the workflow plan
    plan = await get_workflow_plan_func(workflow_id, parameters)
    
    # 2. Agent memory: track progress
    completed_steps = {}
    remaining_steps = plan["steps"].copy()
    
    # 3. Execute steps until done
    while remaining_steps:
        # Find next executable step (dependencies met)
        next_step = find_next_executable_step(remaining_steps, completed_steps)
        
        if not next_step:
            # All remaining steps are blocked by dependencies
            break
        
        # Generate command for this step
        command = await generate_command_for_step(
            next_step, 
            completed_steps, 
            suggest_aws_commands_func,
            next_step.get("context", {})
        )
        
        # Execute the command directly with call_aws
        result = await call_aws_func(command)
        
        # Wrap result with step metadata
        step_result = {
            "step_id": next_step["step_id"],
            "command": command,
            "result": result,
            "completed_at": datetime.now().isoformat()
        }
        
        # Update agent memory
        completed_steps[next_step["step_id"]] = step_result
        remaining_steps.remove(next_step)
    
    # 4. Return final results
    return {
        "workflow_id": workflow_id,
        "status": "completed" if not remaining_steps else "partial",
        "parameters": parameters,
        "completed_steps": completed_steps,
        "remaining_steps": [step["step_id"] for step in remaining_steps] if remaining_steps else [],
        "metadata": plan.get("metadata", {})
    }


def analyze_workflow_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze workflow plan to provide execution insights."""
    
    steps = plan.get("steps", [])
    
    # Find steps with no dependencies (can run first)
    initial_steps = [step for step in steps if not step.get("depends_on")]
    
    # Build dependency graph
    dependency_graph = {}
    for step in steps:
        step_id = step["step_id"]
        dependencies = step.get("depends_on", [])
        dependency_graph[step_id] = dependencies
    
    # Calculate execution order
    execution_order = []
    remaining = {step["step_id"]: step for step in steps}
    
    while remaining:
        # Find steps that can run now
        ready_steps = [
            step_id for step_id in remaining.keys()
            if all(dep not in remaining for dep in dependency_graph[step_id])
        ]
        
        if not ready_steps:
            break  # Circular dependency or other issue
        
        # Add ready steps to execution order
        for step_id in ready_steps:
            execution_order.append(step_id)
            del remaining[step_id]
    
    return {
        "total_steps": len(steps),
        "initial_steps": [step["step_id"] for step in initial_steps],
        "execution_order": execution_order,
        "has_dependencies": any(step.get("depends_on") for step in steps),
        "workflow_metadata": plan.get("metadata", {})
    } 