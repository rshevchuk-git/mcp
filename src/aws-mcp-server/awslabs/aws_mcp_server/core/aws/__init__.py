"""AWS-specific functionality for the AWS MCP server."""

from .driver import translate_cli_to_ir
from .regions import GLOBAL_SERVICE_REGIONS
from .service import (
    check_for_consent,
    get_local_credentials,
    interpret_command,
    is_operation_read_only,
)

__all__ = [
    'translate_cli_to_ir',
    'GLOBAL_SERVICE_REGIONS',
    'check_for_consent',
    'get_local_credentials',
    'interpret_command',
    'is_operation_read_only',
]
