from constants import LOGICAL_CLOCK_FIELD, PAYLOAD_FIELD, STATUS_FIELD
from errors import UnexpectedReferenceResponse
from models import ResponseStatus
from schemas.request_schema import is_valid_logical_clock

KNOWN_RESPONSE_STATUSES = tuple(status.value for status in ResponseStatus)


def reference_response_from(decoded_message: object) -> dict:
    if type(decoded_message) is not dict:
        raise UnexpectedReferenceResponse(decoded_message)

    if decoded_message.get(STATUS_FIELD) not in KNOWN_RESPONSE_STATUSES:
        raise UnexpectedReferenceResponse(decoded_message)

    if not is_valid_logical_clock(decoded_message.get(LOGICAL_CLOCK_FIELD)):
        raise UnexpectedReferenceResponse(decoded_message)

    if type(decoded_message.get(PAYLOAD_FIELD)) is not dict:
        raise UnexpectedReferenceResponse(decoded_message)

    return decoded_message
