from datetime import datetime, timedelta

from constants import TIMESTAMP_FIELD
from schemas import is_valid_timestamp

RECEIVED_LABEL = "RECEIVED"
SENT_LABEL = "SENT"
RANK_LABEL = "RANK"
SERVERS_LABEL = "SERVERS"
CLOCK_LABEL = "CLOCK"
BERKELEY_LABEL = "BERKELEY"
ELECTION_LABEL = "ELECTION"
TIMEOUT_LABEL = "TIMEOUT"
IGNORED_LABEL = "IGNORED"
LABEL_WIDTH = len(RECEIVED_LABEL)
FIELD_SEPARATOR = " | "
UTC_DESIGNATOR = "Z"
UNIX_EPOCH = datetime(1970, 1, 1)


def print_received_message(decoded_message: object) -> None:
    print_line(RECEIVED_LABEL, described_message(decoded_message))


def print_received_undecodable_bytes(encoded_message: bytes) -> None:
    print_line(RECEIVED_LABEL, f"undecodable bytes={encoded_message.hex()}")


def print_received_publication(topic: str, decoded_message: object) -> None:
    print_line(RECEIVED_LABEL, f"topic={topic!r}{FIELD_SEPARATOR}{described_message(decoded_message)}")


def print_sent_message(message_fields: dict) -> None:
    print_line(SENT_LABEL, described_message(message_fields))


def print_sent_publication(topic: str, publication_fields: dict) -> None:
    print_line(SENT_LABEL, f"topic={topic!r}{FIELD_SEPARATOR}{described_message(publication_fields)}")


def print_ignored_announcement(reason: str) -> None:
    print_line(IGNORED_LABEL, reason)


def print_rank(rank: int) -> None:
    print_line(RANK_LABEL, f"this server received rank={rank} from the reference")


def print_available_servers(available_servers: list) -> None:
    print_line(SERVERS_LABEL, f"available servers={available_servers!r}")


def print_clock_synchronization(
    coordinator_name: str, offset_before_ms: int, offset_after_ms: int, round_trip_ms: int
) -> None:
    print_line(
        CLOCK_LABEL,
        FIELD_SEPARATOR.join(
            [
                f"physical clock synchronized with the coordinator {coordinator_name!r}",
                f"offset_before_ms={offset_before_ms}",
                f"offset_after_ms={offset_after_ms}",
                f"round_trip_ms={round_trip_ms}",
            ]
        ),
    )


def print_berkeley_round(requester_name: str, requester_offset_ms: int, adjustment_ms: int, offset_after_ms: int) -> None:
    print_line(
        BERKELEY_LABEL,
        FIELD_SEPARATOR.join(
            [
                f"clock of {requester_name!r} was {requester_offset_ms} ms from this coordinator",
                f"average adjustment_ms={adjustment_ms}",
                f"coordinator offset_after_ms={offset_after_ms}",
            ]
        ),
    )


def print_election_started(higher_ranked_server_names: list[str]) -> None:
    print_line(ELECTION_LABEL, f"started by this server | asking higher ranked servers={higher_ranked_server_names!r}")


def print_election_postponed() -> None:
    print_line(ELECTION_LABEL, "postponed: this server has no rank yet")


def print_waiting_for_coordinator() -> None:
    print_line(ELECTION_LABEL, "a higher ranked server answered OK | waiting for its announcement on 'servers'")


def print_became_coordinator() -> None:
    print_line(ELECTION_LABEL, "no higher ranked server answered | this server is now the coordinator")


def print_announced_coordinator(coordinator_name: str) -> None:
    print_line(ELECTION_LABEL, f"announcement received | coordinator={coordinator_name!r}")


def print_unavailable(unavailable_error: Exception) -> None:
    print_line(TIMEOUT_LABEL, str(unavailable_error))


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
