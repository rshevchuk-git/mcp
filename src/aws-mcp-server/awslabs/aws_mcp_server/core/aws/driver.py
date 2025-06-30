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

import botocore.exceptions
import jmespath
from ..common.constraints import Constraint, verify_constraints_on_ir
from ..common.errors import (
    CliParsingError,
    CommandValidationError,
    MissingContextError,
)
from ..common.helpers import as_json
from ..common.models import InterpretedProgram, IRTranslation
from ..parser.classifier import classify_operation
from ..parser.interpretation import interpret
from ..parser.parser import parse
from .regions import GLOBAL_SERVICE_REGIONS
from jmespath.exceptions import ParseError
from loguru import logger


def translate_cli_to_ir(cli_command: str) -> IRTranslation:
    """Translate the given CLI command to a Python program.

    The returned payload contains the final Python program
    if the translation was successful or reasons on why
    the translation could not happen.

    Failure reasons have two categories: syntactical (usually
    cased by LLM hallucinations) and validations (usually
    due to a lack of required parameters or invalid parameter
    values).

    Syntactical errors can be used for a refinement loop, while validations
    errors can be used to ask for more clarification from the end-user.
    """
    try:
        command = parse(cli_command)
    except (CliParsingError, CommandValidationError) as exc:
        return IRTranslation(validation_failures=[exc.as_failure()])
    except MissingContextError as exc:
        classification = classify_operation(
            exc.command_metadata.service_sdk_name,
            exc.command_metadata.operation_sdk_name,
        )
        return IRTranslation(
            missing_context_failures=[exc.as_failure()],
            command_metadata=exc.command_metadata,
            classification=classification,
        )

    classification = classify_operation(command.service_name, command.operation_name)
    return IRTranslation(
        command=command,
        command_metadata=command.command_metadata,
        classification=classification,
    )


def interpret_command(
    cli_command: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    constraints: list[Constraint],
    default_region: str,
    max_results: int | None = None,
    max_tokens: int | None = None,
    is_counting: bool | None = None,
) -> InterpretedProgram:
    """Interpret the CLI command.

    The interpretation validates the CLI command and translates it
    to an intermediate representation that can be interpreted.

    The response contains any validation errors found during
    validating the command, as well as any errors that occur during interpretation.
    """
    if not constraints:
        raise ValueError('Cannot interpret commands without default constraints')
    translation = translate_cli_to_ir(cli_command)

    if translation.command is None:
        return InterpretedProgram(translation=translation)

    region = translation.command.region or default_region
    if (
        translation.command.command_metadata.service_sdk_name in GLOBAL_SERVICE_REGIONS
        and region != GLOBAL_SERVICE_REGIONS[translation.command.command_metadata.service_sdk_name]
    ):
        region = GLOBAL_SERVICE_REGIONS[translation.command.command_metadata.service_sdk_name]

    client_side_query = translation.command.client_side_query
    client_side_filter = None

    if client_side_query is not None:
        try:
            client_side_filter = jmespath.compile(client_side_query)
        except ParseError as error:
            logger.info('Ignoring client-side filter: {}', client_side_query)
            logger.error('Client-side filter parsing error: {}', str(error))

    failed_constraints = verify_constraints_on_ir(translation, constraints)
    if failed_constraints:
        return InterpretedProgram(
            translation=translation, failed_constraints=failed_constraints, region_name=region
        )

    try:
        response = interpret(
            translation.command,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            region=region,
            client_side_filter=client_side_filter,
            max_results=max_results,
            max_tokens=max_tokens,
            is_counting=is_counting,
        )
    except botocore.exceptions.ClientError as error:
        service_error = str(error)
        status_code = error.response['ResponseMetadata']['HTTPStatusCode']
        error_code = error.response['Error']['Code']
        return InterpretedProgram(
            translation=translation,
            service_error=service_error,
            status_code=status_code,
            error_code=error_code,
            region_name=region,
        )

    payload = as_json(response)
    if (
        translation.command.region is None
        and translation.command.service_name == 's3'
        and translation.command.operation_python_name == 'list_buckets'
    ):
        region = 'Global'

    if (
        translation.command.service_name == 's3'
        and translation.command.operation_python_name == 'get_bucket_location'
    ):
        region = response['LocationConstraint']

    return InterpretedProgram(
        translation=translation,
        response=payload,
        status_code=response['ResponseMetadata']['HTTPStatusCode'],
        region_name=region,
        pagination_token=response.get('pagination_token'),
    )
