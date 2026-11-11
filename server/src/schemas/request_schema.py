from constants import (
    CHANNEL_FIELD,
    CHANNEL_NAME_PATTERN,
    LOGICAL_CLOCK_FIELD,
    MAX_MESSAGE_LENGTH,
    MESSAGE_FIELD,
    MIN_MESSAGE_LENGTH,
    OPERATION_FIELD,
    PAYLOAD_FIELD,
    RESERVED_CHANNEL_NAMES,
    SENDER_FIELD,
    TIMESTAMP_FIELD,
    USERNAME_PATTERN,
)
from dtos import RequestMessage
from errors import InvalidChannelName, InvalidMessage, InvalidUsername, UnknownOperation
from models import Operation
from schemas.envelope_schema import refuse_malformed_envelope

KNOWN_OPERATION_NAMES = tuple(operation.value for operation in Operation)
OPERATIONS_NAMING_A_CHANNEL = (Operation.CREATE_CHANNEL, Operation.PUBLISH)


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
        logical_clock=decoded_message[LOGICAL_CLOCK_FIELD],
        payload=decoded_message[PAYLOAD_FIELD],
    )


def refuse_unknown_operation(operation_name: str) -> None:
    if operation_name not in KNOWN_OPERATION_NAMES:
        raise UnknownOperation()


def refuse_invalid_username(username: str) -> None:
    if USERNAME_PATTERN.fullmatch(username) is None:
        raise InvalidUsername()


def refuse_invalid_channel_name(channel_name: object) -> None:
    if type(channel_name) is not str or CHANNEL_NAME_PATTERN.fullmatch(channel_name) is None:
        raise InvalidChannelName()

    if channel_name in RESERVED_CHANNEL_NAMES:
        raise InvalidChannelName()


def refuse_invalid_message(message: object) -> None:
    if type(message) is not str or not MIN_MESSAGE_LENGTH <= len(message) <= MAX_MESSAGE_LENGTH:
        raise InvalidMessage()
