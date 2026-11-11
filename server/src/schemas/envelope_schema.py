from constants import (
    LOGICAL_CLOCK_FIELD,
    MAX_LOGICAL_CLOCK,
    MAX_TIMESTAMP_MS,
    MIN_LOGICAL_CLOCK,
    MIN_TIMESTAMP_MS,
    OPERATION_FIELD,
    PAYLOAD_FIELD,
    SENDER_FIELD,
    TIMESTAMP_FIELD,
    UNIDENTIFIED_OPERATION,
)
from errors import MalformedMessage

REQUIRED_FIELD_TYPES = {
    OPERATION_FIELD: str,
    SENDER_FIELD: str,
    TIMESTAMP_FIELD: int,
    LOGICAL_CLOCK_FIELD: int,
    PAYLOAD_FIELD: dict,
}


def is_valid_timestamp(timestamp: object) -> bool:
    return type(timestamp) is int and MIN_TIMESTAMP_MS <= timestamp <= MAX_TIMESTAMP_MS


def is_valid_logical_clock(logical_clock: object) -> bool:
    return type(logical_clock) is int and MIN_LOGICAL_CLOCK <= logical_clock <= MAX_LOGICAL_CLOCK


def valid_logical_clock_of(decoded_message: object) -> int | None:
    if type(decoded_message) is not dict:
        return None

    received_logical_clock = decoded_message.get(LOGICAL_CLOCK_FIELD)
    if is_valid_logical_clock(received_logical_clock):
        return received_logical_clock

    return None


def operation_label_of(decoded_message: object, known_operation_names: tuple[str, ...]) -> str:
    if type(decoded_message) is not dict:
        return UNIDENTIFIED_OPERATION

    operation_name = decoded_message.get(OPERATION_FIELD)
    if operation_name in known_operation_names:
        return operation_name

    return UNIDENTIFIED_OPERATION


def refuse_malformed_envelope(decoded_message: object) -> None:
    if type(decoded_message) is not dict:
        raise MalformedMessage()

    for field_name, field_type in REQUIRED_FIELD_TYPES.items():
        if type(decoded_message.get(field_name)) is not field_type:
            raise MalformedMessage()

    if not is_valid_timestamp(decoded_message[TIMESTAMP_FIELD]):
        raise MalformedMessage()

    if not is_valid_logical_clock(decoded_message[LOGICAL_CLOCK_FIELD]):
        raise MalformedMessage()
