#!/usr/bin/env python3
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

"""Script to compile and index sample workflows."""

import asyncio
from pathlib import Path
from loguru import logger

from ..workflows.compiler import compiler
from ..workflows.storage import initialize_storage
from ..workflows.discovery import discovery


async def compile_and_index_workflows():
    """Compile and index sample workflows."""
    # Initialize storage
    workflows_dir = Path(__file__).parent.parent / "workflows_registry"
    initialize_storage(workflows_dir)
    
    # Compile sample workflows
    community_dir = workflows_dir / "community"
    compiled_count = 0
    
    for yaml_file in community_dir.glob("*.yaml"):
        try:
            compiled = compiler.compile_from_file(yaml_file)
            logger.info(f"Compiled workflow: {compiled.workflow_id}")
            compiled_count += 1
        except Exception as e:
            logger.error(f"Failed to compile {yaml_file.name}: {e}")
    
    logger.info(f"Compiled {compiled_count} workflows")
    
    # Index workflows for discovery
    await discovery.index_workflows()
    logger.info("Indexed workflows for discovery")


if __name__ == "__main__":
    asyncio.run(compile_and_index_workflows())