import argparse
import tempfile
from awslabs.aws_mcp_server.core.kb.generate_embeddings import (
    generate_embeddings,
)
from pathlib import Path
from unittest.mock import MagicMock, patch


@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.driver._get_command_table')
@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.logger')
def test_generate_embeddings_handles_exceptions(mock_logger, mock_get_command_table):
    """Test that exceptions during document retrieval are handled gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        model_name = 'BAAI/bge-base-en-v1.5'
        cache_file = cache_dir / f'{model_name.replace("/", "-")}.npz'

        # Create a dummy cache file
        cache_file.touch()

        # Mock service command instance with spec to pass isinstance check
        from awscli.clidriver import ServiceCommand

        mock_service_command = MagicMock(spec=ServiceCommand)
        mock_service_command._get_command_table.side_effect = Exception('Test exception')

        mock_get_command_table.return_value = {'failing-service': mock_service_command}

        generate_embeddings(model_name, cache_dir, overwrite=True)

        # Should not raise exception and log 0 documents retrieved
        mock_logger.info.assert_any_call('Collected 0 documents.')


def test_generate_embeddings_cache_exists_no_overwrite():
    """Test generate_embeddings when cache exists and overwrite is False."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        model_name = 'BAAI/bge-base-en-v1.5'
        cache_file = cache_dir / f'{model_name.replace("/", "-")}.npz'

        # Create a dummy cache file
        cache_file.touch()

        with patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.logger') as mock_logger:
            generate_embeddings(model_name, cache_dir, overwrite=False)

            # Should log that embeddings already exist
            mock_logger.info.assert_called_with(
                f'Embeddings are already generated and cached: {cache_file}. Use --overwrite to regenerate.'
            )


@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings._get_aws_api_documents')
@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.DenseRetriever')
@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.logger')
def test_generate_embeddings_overwrite_existing(
    mock_logger, mock_dense_retriever, mock_get_aws_api_documents
):
    """Test generate_embeddings with overwrite=True."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        model_name = 'BAAI/bge-base-en-v1.5'
        cache_file = cache_dir / f'{model_name.replace("/", "-")}.npz'

        # Create a dummy cache file
        cache_file.touch()

        # Mock documents
        mock_documents = [
            {'command': 'aws ec2 describe-instances', 'description': 'Test', 'parameters': {}}
        ]
        mock_get_aws_api_documents.return_value = mock_documents

        # Mock retriever
        mock_retriever_instance = MagicMock()
        mock_dense_retriever.return_value = mock_retriever_instance

        generate_embeddings(model_name, cache_dir, overwrite=True)

        # Should log overwrite message
        mock_logger.info.assert_any_call(f'Overwriting existing cached embeddings: {cache_file}')

        # Should create retriever and generate index
        mock_dense_retriever.assert_called_once_with(model_name=model_name, cache_dir=cache_dir)
        mock_retriever_instance.generate_index.assert_called_once_with(mock_documents)
        mock_retriever_instance.save_to_cache.assert_called_once()


@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.driver._get_command_table')
@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.logger')
@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.DenseRetriever')
def test_generate_embeddings_with_document_details(
    mock_dense_retriever, mock_logger, mock_get_command_table
):
    """Test generate_embeddings() processes document correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        model_name = 'BAAI/bge-base-en-v1.5'
        cache_file = cache_dir / f'{model_name.replace("/", "-")}.npz'

        # Create a dummy cache file
        cache_file.touch()

        # Mock input shape
        mock_member = MagicMock()
        mock_member.type_name = 'string'
        mock_member.documentation = '<p>Mock inner documentation</p>'

        mock_input_shape = MagicMock()
        mock_input_shape.members = {'MockParam': mock_member}

        # Mock operation
        mock_operation = MagicMock()
        mock_operation._operation_model.documentation = (
            '<p>Deletes the specified alternate contact.</p>'
        )
        mock_operation._operation_model.input_shape = mock_input_shape

        # Mock service command instance with spec to pass isinstance check
        from awscli.clidriver import ServiceCommand

        mock_service_command = MagicMock(spec=ServiceCommand)
        mock_service_command._get_command_table.return_value = {'mock-operation': mock_operation}

        mock_get_command_table.return_value = {'mock-service': mock_service_command}

        # Mock DenseRetriever
        mock_retriever_instance = MagicMock()
        mock_dense_retriever.return_value = mock_retriever_instance

        generate_embeddings(model_name, cache_dir, overwrite=True)

        mock_logger.info('Collected 1 documents.')

        mock_dense_retriever.assert_called_once_with(model_name=model_name, cache_dir=cache_dir)

        mock_retriever_instance.generate_index.assert_called_once()
        mock_retriever_instance.save_to_cache.assert_called_once()


def test_argument_parser_defaults():
    """Test that argument parser has correct defaults."""
    parser = argparse.ArgumentParser(description='Argument parser for model loading')
    parser.add_argument(
        '--model-name',
        type=str,
        default='BAAI/bge-base-en-v1.5',
        help='Name or path of the model to load',
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        default=str(Path(__file__).resolve().parent.parent / 'data' / 'embeddings'),
        help='Directory to use for caching models',
    )
    parser.add_argument(
        '--overwrite', action='store_true', help='Overwrite existing cached files (default: False)'
    )

    args = parser.parse_args([])

    assert args.model_name == 'BAAI/bge-base-en-v1.5'
    assert args.overwrite is False
    assert 'embeddings' in args.cache_dir
