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

"""JSON workflow validator with real-time validation and helpful error messages."""

import json
import jsonschema
from loguru import logger
from pathlib import Path
from typing import Any, Dict, List, Tuple


class WorkflowJSONValidator:
    """Validates JSON workflow definitions against schema."""

    def __init__(self):
        """Initialize the validator."""
        self.schema_path = Path(__file__).parent / 'schema.json'
        self.schema = self._load_schema()

    def get_validation_summary(self, file_path: Path) -> str:
        """Get a comprehensive validation summary for a workflow file."""
        is_valid, errors = self.validate_file(file_path)

        if is_valid:
            return f'✅ {file_path.name} is valid'

        summary = f'❌ {file_path.name} has validation errors:\n'
        for i, error in enumerate(errors, 1):
            summary += f'  {i}. {error}\n'

        return summary

    def validate_json(self, json_content: str) -> Tuple[bool, List[str]]:
        """Validate JSON content against the schema.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # Parse JSON
            data = json.loads(json_content)

            # Validate against schema
            validator = jsonschema.Draft202012Validator(self.schema)
            errors = list(validator.iter_errors(data))

            if not errors:
                return True, []

            # Format error messages
            error_messages = []
            for error in errors:
                path = ' -> '.join(str(p) for p in error.path)
                message = f'{path}: {error.message}'
                if error.context:
                    message += f' (context: {error.context[0].message})'
                error_messages.append(message)

            return False, error_messages

        except json.JSONDecodeError as e:
            return False, [f'Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}']
        except Exception as e:
            return False, [f'Validation error: {str(e)}']

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate a JSON workflow file.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return self.validate_json(content)
        except FileNotFoundError:
            return False, [f'File not found: {file_path}']
        except Exception as e:
            return False, [f'Error reading file: {str(e)}']

    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema for workflow validation."""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'Failed to load schema: {e}')
            raise


# Global validator instance
validator = WorkflowJSONValidator()
