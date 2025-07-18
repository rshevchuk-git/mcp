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

"""Workflow data models for the POC."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import json


class WorkflowParameter(BaseModel):
    """Workflow parameter definition."""
    name: str
    type: str = "string"
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None


class WorkflowStep(BaseModel):
    """Individual workflow step."""
    id: str
    type: str  # "command", "wait", etc.
    intent: Optional[str] = None  # Natural language intent for command steps
    context: Optional[Dict[str, Any]] = None  # Context for command generation
    timeout: Optional[int] = None
    depends_on: Optional[List[str]] = None


class WorkflowSecurity(BaseModel):
    """Security configuration for workflow."""
    required_permissions: List[str] = Field(default_factory=list)
    max_duration: int = 600  # 10 minutes default
    tier: str = "community"


class WorkflowMetadata(BaseModel):
    """Workflow metadata."""
    name: str
    version: str = "1.0"
    description: str
    author: str
    created_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class WorkflowDefinition(BaseModel):
    """Complete workflow definition (source YAML format)."""
    name: str
    version: str = "1.0"
    description: str
    author: str
    parameters: List[WorkflowParameter] = Field(default_factory=list)
    steps: List[WorkflowStep]
    security: Optional[WorkflowSecurity] = None
    
    def to_embedding_text(self) -> str:
        """Generate text for embeddings."""
        tags_text = " ".join(getattr(self, 'tags', []))
        params_text = " ".join([p.name for p in self.parameters])
        steps_text = " ".join([step.intent or step.id for step in self.steps])
        
        return f"{self.name} {self.description} {tags_text} {params_text} {steps_text}"


class CompiledWorkflow(BaseModel):
    """Compiled workflow (immutable bytecode format)."""
    version: str = "1.0"
    format: str = "aws-mcp-bytecode"
    workflow_id: str
    checksum: str
    metadata: WorkflowMetadata
    parameters: Dict[str, Dict[str, Any]]  # Flattened parameter definitions
    execution_plan: List[Dict[str, Any]]  # Compiled steps
    required_permissions: List[str]
    security: Dict[str, Any]
    
    @classmethod
    def from_definition(cls, definition: WorkflowDefinition) -> "CompiledWorkflow":
        """Compile a workflow definition into bytecode."""
        # Generate workflow ID
        workflow_id = f"{definition.name.replace('-', '_')}_v{definition.version.replace('.', '_')}"
        
        # Flatten parameters
        parameters = {}
        for param in definition.parameters:
            parameters[param.name] = {
                "type": param.type,
                "required": param.required,
                "default": param.default,
                "description": param.description
            }
        
        # Compile steps to execution plan
        execution_plan = []
        for step in definition.steps:
            compiled_step = {
                "step_id": step.id,
                "type": step.type,
                "timeout": step.timeout or 300,  # 5 minute default
            }
            
            if step.intent:
                compiled_step["intent"] = step.intent
            if step.context:
                compiled_step["context"] = step.context
            if step.depends_on:
                compiled_step["depends_on"] = step.depends_on
                
            execution_plan.append(compiled_step)
        
        # Extract security info
        security_config = definition.security or WorkflowSecurity()
        security = {
            "tier": security_config.tier,
            "max_duration": security_config.max_duration,
            "validated": True,
            "risk_score": 2.5  # Default for POC
        }
        
        # Create metadata
        metadata = WorkflowMetadata(
            name=definition.name,
            version=definition.version,
            description=definition.description,
            author=definition.author,
            created_at=datetime.utcnow(),
            tags=getattr(definition, 'tags', [])
        )
        
        # Generate checksum
        content_for_hash = {
            "workflow_id": workflow_id,
            "metadata": metadata.model_dump(),
            "parameters": parameters,
            "execution_plan": execution_plan,
            "required_permissions": security_config.required_permissions
        }
        checksum = hashlib.sha256(
            json.dumps(content_for_hash, sort_keys=True).encode()
        ).hexdigest()
        
        return cls(
            workflow_id=workflow_id,
            checksum=checksum,
            metadata=metadata,
            parameters=parameters,
            execution_plan=execution_plan,
            required_permissions=security_config.required_permissions,
            security=security
        )


class WorkflowExecution(BaseModel):
    """Runtime workflow execution state."""
    execution_id: str
    workflow_id: str
    parameters: Dict[str, Any]
    status: str = "running"  # running, completed, failed
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WorkflowSuggestion(BaseModel):
    """Workflow suggestion from discovery."""
    workflow_id: str
    name: str
    description: str
    author: str
    similarity: float
    required_permissions: List[str]
    parameters: List[WorkflowParameter]