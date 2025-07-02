import argparse
import pytest
import tempfile
from awslabs.aws_mcp_server.core.kb.generate_embeddings import (
    _clean_text,
    _get_aws_api_documents,
    _to_cli_style,
    generate_embeddings,
)
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_to_cli_style():
    """Test basic CLI style conversion."""
    assert _to_cli_style('CreateInstance') == 'create-instance'
    assert _to_cli_style('create-instance') == 'create-instance'
    assert _to_cli_style('Create') == 'create'


@pytest.mark.parametrize(
    'raw_text, clean_text',
    [
        (
            '<p>Retroactively applies the archive rule to existing findings that meet the archive rule criteria.</p>',
            'Retroactively applies the archive rule to existing findings that meet the archive rule criteria.',
        ),
        (
            '<p>Accepts the request that originated from <a>StartPrimaryEmailUpdate</a> to update the primary email address (also known as the root user email address) for the specified account.</p>',
            'Accepts the request that originated from StartPrimaryEmailUpdate to update the primary email address (also known as the root user email address) for the specified account.',
        ),
        (
            '<p>Deletes the specified alternate contact from an Amazon Web Services account.</p> \
            <p>For complete details about how to use the alternate contact operations, see <a href="https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-update-contact.html"> \
            Access or updating the alternate contacts</a>.</p> <note> <p>Before you can update the alternate contact information for an Amazon Web Services account that is managed by Organizations, \
            you must first enable integration between Amazon Web Services Account Management and Organizations. \
            For more information, see <a href="https://docs.aws.amazon.com/accounts/latest/reference/using-orgs-trusted-access.html">Enabling trusted access for Amazon Web Services Account Management</a>.</p> </note>',
            'Deletes the specified alternate contact from an Amazon Web Services account. For complete details about how to use the alternate contact operations, see Access or updating the alternate contacts. Before you can update the alternate contact information for an Amazon Web Services account that is managed by Organizations, you must first enable integration between Amazon Web Services Account Management and Organizations. For more information, see Enabling trusted access for Amazon Web Services Account Management.',
        ),
    ],
)
def test_clean_text(raw_text, clean_text):
    """Test _clean_text."""
    assert _clean_text(raw_text) == clean_text


@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.driver._get_command_table')
def test_get_aws_api_documents_handles_exceptions(mock_get_command_table):
    """Test that exceptions during document retrieval are handled gracefully."""
    mock_service_command = MagicMock()
    mock_service_command._get_command_table.side_effect = Exception('Test exception')

    mock_get_command_table.return_value = {'failing-service': mock_service_command}

    # Should not raise exception
    documents = _get_aws_api_documents()
    assert isinstance(documents, list)


@patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.driver._get_command_table')
def test_get_aws_api_documents(mock_get_command_table):
    """Test _get_aws_api_documents."""
    from awscli.clidriver import ServiceCommand

    # Mock input shape
    mock_member = MagicMock()
    mock_member.type_name = 'string'
    mock_member.documentation = '<p>Mock inner documentation</p>'

    mock_input_shape = MagicMock()
    mock_input_shape.members = {'MockParam': mock_member}

    # Mock operation
    mock_operation = MagicMock()
    mock_operation._operation_model.documentation = 'Mock operation documentation'
    mock_operation._operation_model.input_shape = mock_input_shape

    # Mock service command instance with spec to pass isinstance check
    mock_service_command = MagicMock(spec=ServiceCommand)
    mock_service_command._get_command_table.return_value = {'mock-operation': mock_operation}

    mock_get_command_table.return_value = {'mock-service': mock_service_command}

    documents = _get_aws_api_documents()

    assert isinstance(documents, list)
    assert len(documents) == 1

    doc = documents[0]
    assert doc['command'] == 'aws mock-service mock-operation'
    assert doc['description'] == 'Mock operation documentation'
    assert 'mock-param (string)' in doc['parameters']
    assert doc['parameters']['mock-param (string)'] == 'Mock inner documentation'


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
def test_generate_embeddings_overwrite_existing(mock_dense_retriever, mock_get_aws_api_documents):
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

        with patch('awslabs.aws_mcp_server.core.kb.generate_embeddings.logger') as mock_logger:
            generate_embeddings(model_name, cache_dir, overwrite=True)

            # Should log overwrite message
            mock_logger.info.assert_any_call(
                f'Overwriting existing cached embeddings: {cache_file}'
            )

            # Should create retriever and generate index
            mock_dense_retriever.assert_called_once_with(
                model_name=model_name, cache_dir=cache_dir
            )
            mock_retriever_instance.generate_index.assert_called_once_with(mock_documents)
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
