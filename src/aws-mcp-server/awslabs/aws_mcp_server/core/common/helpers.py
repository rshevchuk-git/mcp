import json
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
