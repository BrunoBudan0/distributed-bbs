from datetime import datetime, timedelta

from constants import TIMESTAMP_FIELD
from schemas import is_valid_timestamp

RECEIVED_LABEL = "RECEIVED"
SENT_LABEL = "SENT    "
FIELD_SEPARATOR = " | "
UTC_DESIGNATOR = "Z"
UNIX_EPOCH = datetime(1970, 1, 1)


def print_received_message(decoded_message: object) -> None:
    print_line(RECEIVED_LABEL, described_message(decoded_message))


def print_received_undecodable_bytes(encoded_message: bytes) -> None:
    print_line(RECEIVED_LABEL, f"undecodable bytes={encoded_message.hex()}")


def print_sent_message(message_fields: dict) -> None:
    print_line(SENT_LABEL, described_message(message_fields))


def print_sent_publication(topic: str, publication_fields: dict) -> None:
    print_line(SENT_LABEL, f"topic={topic!r}{FIELD_SEPARATOR}{described_message(publication_fields)}")


def print_line(direction_label: str, description: str) -> None:
    print(f"{direction_label}{FIELD_SEPARATOR}{description}", flush=True)


def described_message(decoded_message: object) -> str:
    if type(decoded_message) is not dict:
        return repr(decoded_message)

    return FIELD_SEPARATOR.join(
        f"{field_name}={described_field(field_name, field_value)}"
        for field_name, field_value in decoded_message.items()
    )


def described_field(field_name: object, field_value: object) -> str:
    if field_name == TIMESTAMP_FIELD and is_valid_timestamp(field_value):
        return readable_timestamp(field_value)

    return repr(field_value)


def readable_timestamp(timestamp_ms: int) -> str:
    moment = UNIX_EPOCH + timedelta(milliseconds=timestamp_ms)
    return f"{moment.isoformat(timespec='milliseconds')}{UTC_DESIGNATOR}"
