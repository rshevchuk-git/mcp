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

"""Workflow discovery system using embeddings."""

import json
from typing import List, Dict, Any
from loguru import logger

from ..core.kb.dense_retriever import DenseRetriever, DEFAULT_CACHE_DIR, DEFAULT_EMBEDDINGS_MODEL
from .models import CompiledWorkflow, WorkflowSuggestion, WorkflowParameter
from .storage import get_storage


class WorkflowDiscovery:
    """Workflow discovery using embeddings."""
    
    def __init__(self, model_name: str = DEFAULT_EMBEDDINGS_MODEL, cache_dir = DEFAULT_CACHE_DIR):
        self.retriever = DenseRetriever(
            top_k=10,  # Get more results for workflows
            model_name=model_name,
            cache_dir=cache_dir
        )
        self._workflow_documents = []
        self._workflows_indexed = False
    
    async def index_workflows(self) -> None:
        """Index all compiled workflows for discovery."""
        try:
            storage = get_storage()
            workflows = await storage.list_compiled_workflows()
            
            # Convert workflows to documents for embeddings
            documents = []
            for workflow in workflows:
                doc = self._workflow_to_document(workflow)
                documents.append(doc)
            
            if documents:
                # Generate embeddings for workflow documents
                self.retriever.generate_index(documents)
                self._workflow_documents = documents
                self._workflows_indexed = True
                logger.info(f"Indexed {len(documents)} workflows for discovery")
            else:
                logger.warning("No workflows found to index")
                
        except Exception as e:
            logger.error(f"Failed to index workflows: {e}")
            raise
    
    def _workflow_to_document(self, workflow: CompiledWorkflow) -> Dict[str, Any]:
        """Convert a compiled workflow to a document for embeddings."""
        # Create embedding text
        embedding_text = self._create_embedding_text(workflow)
        
        # Create parameters list for the document
        parameters = []
        for param_name, param_config in workflow.parameters.items():
            parameters.append({
                "name": param_name,
                "type": param_config.get("type", "string"),
                "required": param_config.get("required", False),
                "description": param_config.get("description", "")
            })
        
        return {
            "type": "workflow",
            "workflow_id": workflow.workflow_id,
            "name": workflow.metadata.name,
            "description": workflow.metadata.description,
            "author": workflow.metadata.author,
            "version": workflow.metadata.version,
            "embedding_text": embedding_text,
            "required_permissions": workflow.required_permissions,
            "parameters": parameters,
            "security": workflow.security,
            "tags": getattr(workflow.metadata, 'tags', [])
        }
    
    def _create_embedding_text(self, workflow: CompiledWorkflow) -> str:
        """Create text for embeddings from workflow."""
        parts = [
            workflow.metadata.name,
            workflow.metadata.description,
            workflow.metadata.author,
        ]
        
        # Add step intents
        for step in workflow.execution_plan:
            if step.get("intent"):
                parts.append(step["intent"])
        
        # Add tags if available
        tags = getattr(workflow.metadata, 'tags', [])
        if tags:
            parts.extend(tags)
        
        # Add parameter names
        parts.extend(workflow.parameters.keys())
        
        return " ".join(parts)
    
    async def suggest_workflows(self, query: str, max_results: int = 5) -> List[WorkflowSuggestion]:
        """Find workflows matching the query."""
        if not self._workflows_indexed:
            await self.index_workflows()
        
        if not self._workflow_documents:
            logger.warning("No workflows indexed for discovery")
            return []
        
        try:
            # Use the existing retriever to search
            results = self.retriever.get_suggestions(query)
            
            suggestions = []
            for doc in results.get('suggestions', [])[:max_results]:
                # Only return workflow documents
                if doc.get('type') != 'workflow':
                    continue
                
                # Convert parameters back to WorkflowParameter objects
                parameters = []
                for param_data in doc.get('parameters', []):
                    parameters.append(WorkflowParameter(**param_data))
                
                suggestion = WorkflowSuggestion(
                    workflow_id=doc['workflow_id'],
                    name=doc['name'],
                    description=doc['description'],
                    author=doc['author'],
                    similarity=doc.get('similarity', 0.0),
                    required_permissions=doc.get('required_permissions', []),
                    parameters=parameters
                )
                suggestions.append(suggestion)
            
            logger.info(f"Found {len(suggestions)} workflow suggestions for query: {query}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to search workflows: {e}")
            return []
    
    async def refresh_index(self) -> None:
        """Refresh the workflow index."""
        self._workflows_indexed = False
        await self.index_workflows()


# Global discovery instance
discovery: WorkflowDiscovery = WorkflowDiscovery()