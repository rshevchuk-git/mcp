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

import json
from .models import Workflow
from awslabs.aws_api_mcp_server.workflows_registry import __file__ as registry_root
from pathlib import Path
from typing import Optional


class WorkflowsRegistry:
    """Workflow registry for AWS API MCP."""

    def __init__(self, workflows_dir: Path):
        """Initialize the registry."""
        self.workflows = {}

        if not workflows_dir.exists():
            raise RuntimeError(f'Workflows directory {workflows_dir} does not exist')

        for file_path in workflows_dir.glob('*.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.workflows[data['name']] = Workflow(**data)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow from file."""
        if workflow_id not in self.workflows:
            return None

        return self.workflows[workflow_id]

    def pretty_print_workflows(self) -> str:
        """Pretty print all workflows."""
        return '\n'.join(
            [
                f'* {workflow.name} : {workflow.short_description}\n'
                for workflow in self.workflows.values()
            ]
        )


registry: Optional[WorkflowsRegistry] = None


def get_workflows_registry() -> WorkflowsRegistry:
    """Get the global registry instance."""
    global registry

    """Get the global registry instance."""
    if registry is None:
        registry = WorkflowsRegistry(Path(registry_root).parent)
    return registry
