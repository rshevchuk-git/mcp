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

import json
import os
import time
from botocore.response import StreamingBody
from contextlib import contextmanager
from datetime import datetime
from loguru import logger
from typing import Any


@contextmanager
def operation_timer(service: str, operation: str):
    """Context manager for timing interpretation calls.

    :param service: The service name.
    :param operation: The operation name.
    """
    start = time.perf_counter()
    logger.info('Starting interpreting operation {}.{}', service, operation)
    yield
    end = time.perf_counter()
    elapsed_time = end - start
    logger.info('Operation {}.{} interpreted in {} seconds', service, operation, elapsed_time)


class Boto3Encoder(json.JSONEncoder):
    """Custom JSON encoder for boto3 objects."""

    def default(self, o):
        """Return a JSON-serializable version of the object."""
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, StreamingBody):
            return o.read().decode('utf-8')

        return super().default(o)


def as_json(boto_response: dict[str, Any]) -> str:
    """Convert a boto3 response dictionary to a JSON string."""
    return json.dumps(boto_response, cls=Boto3Encoder)


def expand_user_home_directory(args: list[str]) -> list[str]:
    """Expand paths beginning with '~' or '~user'."""
    return [os.path.expanduser(arg) for arg in args]
