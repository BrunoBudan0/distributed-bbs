from datetime import datetime, timedelta

from constants import TIMESTAMP_FIELD
from schemas import is_valid_timestamp

RECEIVED_LABEL = "RECEIVED"
SENT_LABEL = "SENT"
RANK_LABEL = "RANK"
SERVERS_LABEL = "SERVERS"
CLOCK_LABEL = "CLOCK"
TIMEOUT_LABEL = "TIMEOUT"
LABEL_WIDTH = len(RECEIVED_LABEL)
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


def print_rank(rank: int) -> None:
    print_line(RANK_LABEL, f"this server received rank={rank} from the reference")


def print_available_servers(available_servers: list) -> None:
    print_line(SERVERS_LABEL, f"available servers={available_servers!r}")


def print_clock_synchronization(offset_before_ms: int, offset_after_ms: int, round_trip_ms: int) -> None:
    print_line(
        CLOCK_LABEL,
        FIELD_SEPARATOR.join(
            [
                "physical clock synchronized with the reference",
                f"offset_before_ms={offset_before_ms}",
                f"offset_after_ms={offset_after_ms}",
                f"round_trip_ms={round_trip_ms}",
            ]
        ),
    )


def print_reference_timeout(reference_timeout: Exception) -> None:
    print_line(TIMEOUT_LABEL, str(reference_timeout))


def print_line(label: str, description: str) -> None:
    print(f"{label.ljust(LABEL_WIDTH)}{FIELD_SEPARATOR}{description}", flush=True)


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
