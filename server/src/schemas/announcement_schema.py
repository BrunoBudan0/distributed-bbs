from constants import COORDINATOR_ANNOUNCEMENT_OPERATION, COORDINATOR_FIELD, OPERATION_FIELD, PAYLOAD_FIELD, SERVER_NAME_PATTERN
from errors import MalformedMessage
from schemas.envelope_schema import refuse_malformed_envelope


def coordinator_name_from(decoded_announcement: object) -> str:
    refuse_malformed_envelope(decoded_announcement)

    if decoded_announcement[OPERATION_FIELD] != COORDINATOR_ANNOUNCEMENT_OPERATION:
        raise MalformedMessage()

    coordinator_name = decoded_announcement[PAYLOAD_FIELD].get(COORDINATOR_FIELD)
    if type(coordinator_name) is not str or SERVER_NAME_PATTERN.fullmatch(coordinator_name) is None:
        raise MalformedMessage()

    return coordinator_name
