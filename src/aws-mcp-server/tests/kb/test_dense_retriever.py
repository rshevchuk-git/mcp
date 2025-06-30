import pytest
from awslabs.aws_mcp_server.core.kb import knowledge_base
from awslabs.aws_mcp_server.core.kb.dense_retriever import (
    DEFAULT_CACHE_DIR,
    DEFAULT_EMBEDDINGS_MODEL,
    DEFAULT_TOP_K,
    DenseRetriever,
)


def test_dense_retriever():
    """Tests if knowledge base uses DenseRetriever by default and can retrieve documents."""
    # Check if embeddings file exists
    cache_file = DEFAULT_CACHE_DIR / f'{DEFAULT_EMBEDDINGS_MODEL.replace("/", "-")}.npz'
    if not cache_file.exists():
        pytest.skip(f'Embeddings file not found: {cache_file}')

    knowledge_base.setup(rag_type='DENSE_RETRIEVER')
    assert isinstance(knowledge_base.rag, DenseRetriever)

    suggestions = knowledge_base.get_suggestions('Describe my ec2 instances')
    suggested_commnads = [s['command'] for s in suggestions['suggestions']]

    assert len(suggested_commnads) == DEFAULT_TOP_K
    assert 'aws ec2 describe-instances' in suggested_commnads
