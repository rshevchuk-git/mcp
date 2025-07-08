from awslabs.aws_mcp_server.core.kb.operations_index import calculate_similarity


def test_calculate_similarity_exact_match():
    """Test similarity calculation for exact matches."""
    query = 'launch ec2 instance'
    description = 'create ec2 instance'
    similarity = calculate_similarity(query, description)
    assert 0.5 < similarity <= 1.0  # Should be high similarity


def test_calculate_similarity_partial_match():
    """Test similarity calculation for partial matches."""
    query = 'create ec2 instance'
    description = 'create an ec2 instance with security groups'
    similarity = calculate_similarity(query, description)
    assert 0.5 < similarity <= 1.0  # Should be high similarity


def test_calculate_similarity_no_match():
    """Test similarity calculation for no matches."""
    query = 'create ec2 instance'
    description = 'delete s3 bucket'
    similarity = calculate_similarity(query, description)
    assert similarity < 0.3  # Should be low similarity
