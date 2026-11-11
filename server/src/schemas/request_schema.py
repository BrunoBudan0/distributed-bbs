from constants import (
    CHANNEL_FIELD,
    CHANNEL_NAME_PATTERN,
    MAX_MESSAGE_LENGTH,
    MAX_TIMESTAMP_MS,
    MESSAGE_FIELD,
    MIN_MESSAGE_LENGTH,
    MIN_TIMESTAMP_MS,
    OPERATION_FIELD,
    PAYLOAD_FIELD,
    SENDER_FIELD,
    TIMESTAMP_FIELD,
    UNIDENTIFIED_OPERATION,
    USERNAME_PATTERN,
)
from dtos import RequestMessage
from errors import InvalidChannelName, InvalidMessage, InvalidUsername, MalformedMessage, UnknownOperation
from models import Operation

REQUIRED_FIELD_TYPES = {
    OPERATION_FIELD: str,
    SENDER_FIELD: str,
    TIMESTAMP_FIELD: int,
    PAYLOAD_FIELD: dict,
}
KNOWN_OPERATION_NAMES = tuple(operation.value for operation in Operation)
OPERATIONS_NAMING_A_CHANNEL = (Operation.CREATE_CHANNEL, Operation.PUBLISH)


def is_valid_timestamp(timestamp: object) -> bool:
    return type(timestamp) is int and MIN_TIMESTAMP_MS <= timestamp <= MAX_TIMESTAMP_MS


def operation_label_of(decoded_message: object) -> str:
    if type(decoded_message) is not dict:
        return UNIDENTIFIED_OPERATION

    operation_name = decoded_message.get(OPERATION_FIELD)
    if operation_name in KNOWN_OPERATION_NAMES:
        return operation_name

    return UNIDENTIFIED_OPERATION


def request_from(decoded_message: object) -> RequestMessage:
    refuse_malformed_envelope(decoded_message)
    refuse_unknown_operation(decoded_message[OPERATION_FIELD])
    refuse_invalid_username(decoded_message[SENDER_FIELD])

    operation = Operation(decoded_message[OPERATION_FIELD])
    if operation in OPERATIONS_NAMING_A_CHANNEL:
        refuse_invalid_channel_name(decoded_message[PAYLOAD_FIELD].get(CHANNEL_FIELD))

    if operation is Operation.PUBLISH:
        refuse_invalid_message(decoded_message[PAYLOAD_FIELD].get(MESSAGE_FIELD))

    return RequestMessage(
        operation=operation,
        sender=decoded_message[SENDER_FIELD],
        timestamp=decoded_message[TIMESTAMP_FIELD],
        payload=decoded_message[PAYLOAD_FIELD],
    )


def refuse_malformed_envelope(decoded_message: object) -> None:
    if type(decoded_message) is not dict:
        raise MalformedMessage()

    for field_name, field_type in REQUIRED_FIELD_TYPES.items():
        if type(decoded_message.get(field_name)) is not field_type:
            raise MalformedMessage()

    if not is_valid_timestamp(decoded_message[TIMESTAMP_FIELD]):
        raise MalformedMessage()


def refuse_unknown_operation(operation_name: str) -> None:
    if operation_name not in KNOWN_OPERATION_NAMES:
        raise UnknownOperation()


def refuse_invalid_username(username: str) -> None:
    if USERNAME_PATTERN.fullmatch(username) is None:
        raise InvalidUsername()


def refuse_invalid_channel_name(channel_name: object) -> None:
    if type(channel_name) is not str or CHANNEL_NAME_PATTERN.fullmatch(channel_name) is None:
        raise InvalidChannelName()


def refuse_invalid_message(message: object) -> None:
    if type(message) is not str or not MIN_MESSAGE_LENGTH <= len(message) <= MAX_MESSAGE_LENGTH:
        raise InvalidMessage()
