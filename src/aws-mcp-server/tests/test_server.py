from awslabs.aws_mcp_server.core.common.errors import AwsMcpError
from awslabs.aws_mcp_server.core.common.models import (
    AwsMcpServerErrorResponse,
    InterpretationResponse,
    ProgramInterpretationResponse,
)
from awslabs.aws_mcp_server.server import call_aws
from botocore.exceptions import NoCredentialsError
from tests.fixtures import TEST_CREDENTIALS, DummyCtx
from unittest.mock import MagicMock, patch


@patch('awslabs.aws_mcp_server.server.DEFAULT_REGION', 'us-east-1')
@patch('awslabs.aws_mcp_server.server.get_local_credentials')
@patch('awslabs.aws_mcp_server.server.interpret_command')
@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
async def test_call_aws_success(
    mock_is_operation_read_only,
    mock_translate_cli_to_ir,
    mock_validate,
    mock_interpret,
    mock_get_creds,
):
    """Test call_aws returns success for a valid read-only command."""
    mock_get_creds.return_value = TEST_CREDENTIALS

    # Create a proper ProgramInterpretationResponse mock
    mock_response = InterpretationResponse(error=None, json='{"Buckets": []}', status_code=200)

    mock_result = ProgramInterpretationResponse(
        response=mock_response,
        metadata=None,
        validation_failures=None,
        missing_context_failures=None,
        failed_constraints=None,
    )
    mock_interpret.return_value = mock_result

    mock_is_operation_read_only.return_value = True

    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    # Mock response with classification as a "read-only" operation
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['read-only']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify - the result should be the ProgramInterpretationResponse object
    assert result == mock_result
    mock_translate_cli_to_ir.assert_called_once_with('aws s3api list-buckets')
    mock_validate.assert_called_once_with(mock_ir)
    mock_get_creds.assert_called_once()
    mock_interpret.assert_called_once()


@patch('awslabs.aws_mcp_server.server.DEFAULT_REGION', 'us-east-1')
@patch('awslabs.aws_mcp_server.server.get_local_credentials')
@patch('awslabs.aws_mcp_server.server.interpret_command')
@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
async def test_call_aws_with_mutating_action(
    mock_is_operation_read_only,
    mock_translate_cli_to_ir,
    mock_validate,
    mock_interpret,
    mock_get_creds,
):
    """Test call_aws with mutating action."""
    mock_get_creds.return_value = TEST_CREDENTIALS

    # Create a proper ProgramInterpretationResponse mock
    mock_response = InterpretationResponse(error=None, json='{"Buckets": []}', status_code=200)

    mock_result = ProgramInterpretationResponse(
        response=mock_response,
        metadata=None,
        validation_failures=None,
        missing_context_failures=None,
        failed_constraints=None,
    )
    mock_interpret.return_value = mock_result

    mock_is_operation_read_only.return_value = False

    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'create-bucket'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    # Mock response with classification that passes validation
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['mutating']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    # Execute
    result = await call_aws('aws s3api create-bucket --bucket somebucket', DummyCtx())

    # Verify that no consent was requested
    assert result == mock_result
    mock_translate_cli_to_ir.assert_called_once_with('aws s3api create-bucket --bucket somebucket')
    mock_validate.assert_called_once_with(mock_ir)
    mock_get_creds.assert_called_once()
    mock_interpret.assert_called_once()


@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
async def test_call_aws_validation_error_awsmcp_error(mock_translate_cli_to_ir):
    """Test call_aws returns error details for AwsMcpError during validation."""
    mock_error = AwsMcpError('Invalid command syntax')
    mock_failure = MagicMock()
    mock_failure.reason = 'Invalid command syntax'
    mock_error.as_failure = MagicMock(return_value=mock_failure)
    mock_translate_cli_to_ir.side_effect = mock_error

    # Execute
    result = await call_aws('aws invalid-service invalid-operation', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while validating the command: Invalid command syntax'
    )
    mock_translate_cli_to_ir.assert_called_once_with('aws invalid-service invalid-operation')


@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
async def test_call_aws_validation_error_generic_exception(mock_translate_cli_to_ir):
    """Test call_aws returns error details for generic exception during validation."""
    mock_translate_cli_to_ir.side_effect = ValueError('Generic validation error')

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while validating the command: Generic validation error'
    )


@patch('awslabs.aws_mcp_server.server.get_local_credentials')
@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
async def test_call_aws_no_credentials_error(
    mock_is_operation_read_only, mock_translate_cli_to_ir, mock_validate, mock_get_creds
):
    """Test call_aws returns error when no AWS credentials are found."""
    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    mock_is_operation_read_only.return_value = True

    # Mock validation response
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['read-only']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    mock_get_creds.side_effect = NoCredentialsError()

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while executing the command: No AWS credentials found. '
        "Please configure your AWS credentials using 'aws configure' "
        'or set appropriate environment variables.'
    )


@patch('awslabs.aws_mcp_server.server.DEFAULT_REGION', 'us-east-1')
@patch('awslabs.aws_mcp_server.server.get_local_credentials')
@patch('awslabs.aws_mcp_server.server.interpret_command')
@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
async def test_call_aws_execution_error_awsmcp_error(
    mock_is_operation_read_only,
    mock_translate_cli_to_ir,
    mock_validate,
    mock_interpret,
    mock_get_creds,
):
    """Test call_aws returns error details for AwsMcpError during execution."""
    mock_get_creds.return_value = TEST_CREDENTIALS

    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    mock_is_operation_read_only.return_value = True

    # Mock validation response
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['read-only']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    mock_error = AwsMcpError('Execution failed')
    mock_failure = MagicMock()
    mock_failure.reason = 'Execution failed'
    mock_error.as_failure = MagicMock(return_value=mock_failure)
    mock_interpret.side_effect = mock_error

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while executing the command: Execution failed'
    )


@patch('awslabs.aws_mcp_server.server.DEFAULT_REGION', 'us-east-1')
@patch('awslabs.aws_mcp_server.server.get_local_credentials')
@patch('awslabs.aws_mcp_server.server.interpret_command')
@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
async def test_call_aws_execution_error_generic_exception(
    mock_is_operation_read_only,
    mock_translate_cli_to_ir,
    mock_validate,
    mock_interpret,
    mock_get_creds,
):
    """Test call_aws returns error details for generic exception during execution."""
    mock_get_creds.return_value = TEST_CREDENTIALS

    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    mock_is_operation_read_only.return_value = True

    # Mock validation response
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['read-only']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    mock_interpret.side_effect = RuntimeError('Generic execution error')

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while executing the command: Generic execution error'
    )


async def test_call_aws_non_aws_command():
    """Test call_aws with command that doesn't start with 'aws'."""
    with patch('awslabs.aws_mcp_server.server.translate_cli_to_ir') as mock_translate_cli_to_ir:
        mock_translate_cli_to_ir.side_effect = ValueError("Command must start with 'aws'")

        result = await call_aws('s3api list-buckets', DummyCtx())

        assert result == AwsMcpServerErrorResponse(
            detail="Error while validating the command: Command must start with 'aws'"
        )


@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
@patch('awslabs.aws_mcp_server.server.is_operation_read_only')
@patch('awslabs.aws_mcp_server.server.READ_OPERATIONS_ONLY_MODE')
async def test_when_operation_is_not_allowed(
    mock_read_operations_only_mode,
    mock_is_operation_read_only,
    mock_translate_cli_to_ir,
    mock_validate,
):
    """Test call_aws returns error when operation is not allowed in read-only mode."""
    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    mock_read_operations_only_mode.return_value = True

    # Mock validation response
    mock_response = MagicMock()
    mock_response.classification = MagicMock()
    mock_response.classification.action_types = ['read-only']
    mock_response.validation_failed = False
    mock_validate.return_value = mock_response

    mock_is_operation_read_only.return_value = False

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # verify
    assert result == AwsMcpServerErrorResponse(
        detail='Execution of this operation is not allowed because read only mode is enabled. It can be disabled by setting the READ_OPERATIONS_ONLY environment variable to False.'
    )


@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
async def test_call_aws_validation_failures(mock_translate_cli_to_ir, mock_validate):
    """Test call_aws returns error for validation failures."""
    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    # Mock validation response with validation failures
    mock_response = MagicMock()
    mock_response.validation_failures = ['Invalid parameter value']
    mock_response.failed_constraints = None
    mock_response.model_dump_json.return_value = (
        '{"validation_failures": ["Invalid parameter value"]}'
    )
    mock_validate.return_value = mock_response

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while validating the command: {"validation_failures": ["Invalid parameter value"]}'
    )
    mock_translate_cli_to_ir.assert_called_once_with('aws s3api list-buckets')
    mock_validate.assert_called_once_with(mock_ir)


@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
async def test_call_aws_failed_constraints(mock_translate_cli_to_ir, mock_validate):
    """Test call_aws returns error for failed constraints."""
    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    # Mock validation response with failed constraints
    mock_response = MagicMock()
    mock_response.validation_failures = None
    mock_response.failed_constraints = ['Resource limit exceeded']
    mock_response.model_dump_json.return_value = (
        '{"failed_constraints": ["Resource limit exceeded"]}'
    )
    mock_validate.return_value = mock_response

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while validating the command: {"failed_constraints": ["Resource limit exceeded"]}'
    )
    mock_translate_cli_to_ir.assert_called_once_with('aws s3api list-buckets')
    mock_validate.assert_called_once_with(mock_ir)


@patch('awslabs.aws_mcp_server.server.validate')
@patch('awslabs.aws_mcp_server.server.translate_cli_to_ir')
async def test_call_aws_both_validation_failures_and_constraints(
    mock_translate_cli_to_ir, mock_validate
):
    """Test call_aws returns error for both validation failures and failed constraints."""
    # Mock IR with command metadata
    mock_ir = MagicMock()
    mock_ir.command_metadata = MagicMock()
    mock_ir.command_metadata.service_sdk_name = 's3api'
    mock_ir.command_metadata.operation_sdk_name = 'list-buckets'
    mock_ir.command = MagicMock()
    mock_ir.command.is_awscli_customization = False  # Ensure interpret_command is called
    mock_translate_cli_to_ir.return_value = mock_ir

    # Mock validation response with both validation failures and failed constraints
    mock_response = MagicMock()
    mock_response.validation_failures = ['Invalid parameter value']
    mock_response.failed_constraints = ['Resource limit exceeded']
    mock_response.model_dump_json.return_value = '{"validation_failures": ["Invalid parameter value"], "failed_constraints": ["Resource limit exceeded"]}'
    mock_validate.return_value = mock_response

    # Execute
    result = await call_aws('aws s3api list-buckets', DummyCtx())

    # Verify
    assert result == AwsMcpServerErrorResponse(
        detail='Error while validating the command: {"validation_failures": ["Invalid parameter value"], "failed_constraints": ["Resource limit exceeded"]}'
    )
    mock_translate_cli_to_ir.assert_called_once_with('aws s3api list-buckets')
    mock_validate.assert_called_once_with(mock_ir)
