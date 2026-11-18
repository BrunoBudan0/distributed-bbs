from constants import (
    CHANNEL_NAME_PATTERN,
    CONTENT_FIELD,
    KIND_FIELD,
    LOGICAL_CLOCK_FIELD,
    MAX_MESSAGE_LENGTH,
    MAX_RECORDS_PER_EXCHANGE,
    MIN_MESSAGE_LENGTH,
    MIN_ORIGIN_SEQUENCE,
    OPERATION_FIELD,
    ORIGIN_SEQUENCE_FIELD,
    ORIGIN_SERVER_FIELD,
    PAYLOAD_FIELD,
    RECORDS_FIELD,
    REPLICATED_RECORD_OPERATION,
    RESERVED_CHANNEL_NAMES,
    SERVER_NAME_PATTERN,
    USERNAME_PATTERN,
    WATERMARKS_FIELD,
)
from errors import InvalidReplicatedRecord, MalformedMessage
from models import RecordKind, ReplicatedRecord
from schemas.envelope_schema import is_valid_logical_clock, is_valid_timestamp, refuse_malformed_envelope

KNOWN_RECORD_KINDS = tuple(kind.value for kind in RecordKind)


def is_server_name(value: object) -> bool:
    return type(value) is str and SERVER_NAME_PATTERN.fullmatch(value) is not None


def is_username(value: object) -> bool:
    return type(value) is str and USERNAME_PATTERN.fullmatch(value) is not None


def is_channel_name(value: object) -> bool:
    return type(value) is str and CHANNEL_NAME_PATTERN.fullmatch(value) is not None and value not in RESERVED_CHANNEL_NAMES


def is_message(value: object) -> bool:
    return type(value) is str and MIN_MESSAGE_LENGTH <= len(value) <= MAX_MESSAGE_LENGTH


def is_origin_sequence(value: object) -> bool:
    return type(value) is int and value >= MIN_ORIGIN_SEQUENCE


CONTENT_FIELD_RULES = {
    RecordKind.LOGIN: {"username": is_username, "logged_in_at_ms": is_valid_timestamp},
    RecordKind.CHANNEL: {
        "name": is_channel_name,
        "created_by_username": is_username,
        "created_at_ms": is_valid_timestamp,
        "created_logical_clock": is_valid_logical_clock,
        "created_on_server": is_server_name,
    },
    RecordKind.PUBLICATION: {
        "channel_name": is_channel_name,
        "author_username": is_username,
        "message": is_message,
        "requested_at_ms": is_valid_timestamp,
        "published_at_ms": is_valid_timestamp,
        "published_by_server": is_server_name,
    },
}


def replicated_record_from(decoded_record: object) -> ReplicatedRecord:
    if type(decoded_record) is not dict:
        raise InvalidReplicatedRecord()

    if not is_server_name(decoded_record.get(ORIGIN_SERVER_FIELD)):
        raise InvalidReplicatedRecord()

    if not is_origin_sequence(decoded_record.get(ORIGIN_SEQUENCE_FIELD)):
        raise InvalidReplicatedRecord()

    if decoded_record.get(KIND_FIELD) not in KNOWN_RECORD_KINDS:
        raise InvalidReplicatedRecord()

    if not is_valid_logical_clock(decoded_record.get(LOGICAL_CLOCK_FIELD)):
        raise InvalidReplicatedRecord()

    kind = RecordKind(decoded_record[KIND_FIELD])
    refuse_invalid_content(kind, decoded_record.get(CONTENT_FIELD))

    return ReplicatedRecord(
        origin_server=decoded_record[ORIGIN_SERVER_FIELD],
        origin_sequence=decoded_record[ORIGIN_SEQUENCE_FIELD],
        kind=kind,
        logical_clock=decoded_record[LOGICAL_CLOCK_FIELD],
        content=decoded_record[CONTENT_FIELD],
    )


def refuse_invalid_content(kind: RecordKind, content: object) -> None:
    field_rules = CONTENT_FIELD_RULES[kind]
    if type(content) is not dict or set(content) != set(field_rules):
        raise InvalidReplicatedRecord()

    for field_name, field_is_valid in field_rules.items():
        if not field_is_valid(content[field_name]):
            raise InvalidReplicatedRecord()


def replicated_records_from(payload: dict) -> list[ReplicatedRecord]:
    decoded_records = payload.get(RECORDS_FIELD)
    if type(decoded_records) is not list or len(decoded_records) > MAX_RECORDS_PER_EXCHANGE:
        raise MalformedMessage()

    return [replicated_record_from(decoded_record) for decoded_record in decoded_records]


def watermarks_from(payload: dict) -> dict[str, int]:
    decoded_watermarks = payload.get(WATERMARKS_FIELD)
    if type(decoded_watermarks) is not dict:
        raise MalformedMessage()

    for origin_server, watermark in decoded_watermarks.items():
        if not is_server_name(origin_server) or type(watermark) is not int or watermark < 0:
            raise MalformedMessage()

    return decoded_watermarks


def replicated_record_message_from(decoded_message: object) -> ReplicatedRecord:
    refuse_malformed_envelope(decoded_message)
    if decoded_message[OPERATION_FIELD] != REPLICATED_RECORD_OPERATION:
        raise MalformedMessage()

    return replicated_record_from(decoded_message[PAYLOAD_FIELD])
