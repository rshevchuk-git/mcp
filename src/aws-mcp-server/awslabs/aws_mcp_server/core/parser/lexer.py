import shlex
from ..common.errors import CliParsingError, ProhibitedOperatorsError


excluded = frozenset(
    {
        '&&',
        '||',
        '=',
        '*=',
        '/=',
        '%=',
        '+=',
        '-=',
        '<<=',
        '>>=',
        '&=',
        '^=',
        '|=',
    }
)


def split_cli_command(cli_command: str) -> list[str]:
    """Split the given CLI command into multiple tokens."""
    try:
        tokens = shlex.split(cli_command)
    except ValueError as e:
        raise CliParsingError(e) from e
    prohibited_tokens = [token for token in tokens if token in excluded]
    if prohibited_tokens:
        raise ProhibitedOperatorsError(prohibited_tokens)
    if not tokens:
        raise CliParsingError('The provided CLI command is empty')
    command = tokens[0]
    if command != 'aws':
        raise CliParsingError('The provided CLI command is not an AWS command')
    return tokens
