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

"""Unit tests for workflow JSON validation."""

from awslabs.aws_api_mcp_server.core.workflows.json_validator import WorkflowJSONValidator
from awslabs.aws_api_mcp_server.workflows_registry import __file__ as registry_root
from pathlib import Path


def test_workflow_validation_summary():
    """Test validation summary for all workflow files."""
    validator = WorkflowJSONValidator()
    workflows_dir = Path(registry_root).parent

    for json_file in workflows_dir.glob('*.json'):
        summary = validator.get_validation_summary(json_file)
        print('summary', summary)
        assert '✅' in summary, f'Workflow {json_file.name} failed validation: {summary}'
