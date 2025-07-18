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

"""Workflow storage abstraction with file-based implementation for POC."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from .models import CompiledWorkflow, WorkflowExecution


class WorkflowStorage(ABC):
    """Abstract workflow storage interface."""
    
    @abstractmethod
    async def save_compiled_workflow(self, workflow: CompiledWorkflow) -> None:
        """Save a compiled workflow."""
        pass
    
    @abstractmethod
    async def get_compiled_workflow(self, workflow_id: str) -> Optional[CompiledWorkflow]:
        """Get a compiled workflow by ID."""
        pass
    
    @abstractmethod
    async def list_compiled_workflows(self) -> List[CompiledWorkflow]:
        """List all compiled workflows."""
        pass
    
    @abstractmethod
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Save workflow execution state."""
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        pass


class FileWorkflowStorage(WorkflowStorage):
    """File-based workflow storage for POC."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.workflows_dir = self.base_dir / "compiled"
        self.executions_dir = self.base_dir / "executions"
        
        # Create directories
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.executions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized file storage at: {self.base_dir}")
    
    async def save_compiled_workflow(self, workflow: CompiledWorkflow) -> None:
        """Save a compiled workflow to file."""
        file_path = self.workflows_dir / f"{workflow.workflow_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(workflow.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Saved compiled workflow: {workflow.workflow_id}")
    
    async def get_compiled_workflow(self, workflow_id: str) -> Optional[CompiledWorkflow]:
        """Get a compiled workflow from file."""
        file_path = self.workflows_dir / f"{workflow_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return CompiledWorkflow(**data)
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_id}: {e}")
            return None
    
    async def list_compiled_workflows(self) -> List[CompiledWorkflow]:
        """List all compiled workflows."""
        workflows = []
        
        for file_path in self.workflows_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                workflow = CompiledWorkflow(**data)
                workflows.append(workflow)
            except Exception as e:
                logger.warning(f"Failed to load workflow from {file_path}: {e}")
                continue
        
        return workflows
    
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Save workflow execution state."""
        file_path = self.executions_dir / f"{execution.execution_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(execution.model_dump(), f, indent=2, default=str)
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        file_path = self.executions_dir / f"{execution_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return WorkflowExecution(**data)
        except Exception as e:
            logger.error(f"Failed to load execution {execution_id}: {e}")
            return None


# Default storage instance - will be initialized in main
storage: Optional[WorkflowStorage] = None


def get_storage() -> WorkflowStorage:
    """Get the global storage instance."""
    if storage is None:
        raise RuntimeError("Workflow storage not initialized")
    return storage


def initialize_storage(base_dir: Path) -> None:
    """Initialize the global storage instance."""
    global storage
    storage = FileWorkflowStorage(base_dir)