import dataclasses


@dataclasses.dataclass(frozen=True)
class CommandMetadata:
    """Metadata for an AWS CLI command, including service and operation names."""

    service_sdk_name: str
    service_full_sdk_name: str | None
    operation_sdk_name: str
    has_streaming_output: bool = False
