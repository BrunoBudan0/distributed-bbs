from constants import LOGICAL_CLOCK_FIELD, OPERATION_FIELD, PAYLOAD_FIELD, SENDER_FIELD, SERVER_NAME_PATTERN, TIMESTAMP_FIELD
from dtos import PeerRequestMessage
from errors import InvalidServerName, UnknownPeerOperation
from models import PeerOperation
from schemas.envelope_schema import refuse_malformed_envelope

KNOWN_PEER_OPERATION_NAMES = tuple(operation.value for operation in PeerOperation)


def peer_request_from(decoded_message: object) -> PeerRequestMessage:
    refuse_malformed_envelope(decoded_message)
    refuse_unknown_peer_operation(decoded_message[OPERATION_FIELD])
    refuse_invalid_server_name(decoded_message[SENDER_FIELD])

    return PeerRequestMessage(
        operation=PeerOperation(decoded_message[OPERATION_FIELD]),
        sender=decoded_message[SENDER_FIELD],
        timestamp=decoded_message[TIMESTAMP_FIELD],
        logical_clock=decoded_message[LOGICAL_CLOCK_FIELD],
        payload=decoded_message[PAYLOAD_FIELD],
    )


def refuse_unknown_peer_operation(operation_name: str) -> None:
    if operation_name not in KNOWN_PEER_OPERATION_NAMES:
        raise UnknownPeerOperation()


def refuse_invalid_server_name(server_name: str) -> None:
    if SERVER_NAME_PATTERN.fullmatch(server_name) is None:
        raise InvalidServerName()
