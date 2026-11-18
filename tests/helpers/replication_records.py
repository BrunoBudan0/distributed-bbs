from helpers.request_exchange import current_timestamp_ms

LOGIN_KIND = "login"
CHANNEL_KIND = "channel"
PUBLICATION_KIND = "publication"
RECORD_LOGICAL_CLOCK = 1


def replicated_record(origin_server: str, origin_sequence: int, kind: str, logical_clock: int, content: dict) -> dict:
    return {
        "origin_server": origin_server,
        "origin_sequence": origin_sequence,
        "kind": kind,
        "logical_clock": logical_clock,
        "content": content,
    }


def login_record(origin_server: str, origin_sequence: int, username: str) -> dict:
    content = {"username": username, "logged_in_at_ms": current_timestamp_ms()}
    return replicated_record(origin_server, origin_sequence, LOGIN_KIND, RECORD_LOGICAL_CLOCK, content)


def channel_record(origin_server: str, origin_sequence: int, channel_name: str, created_logical_clock: int) -> dict:
    content = {
        "name": channel_name,
        "created_by_username": f"creator-on-{origin_server}"[:32],
        "created_at_ms": current_timestamp_ms(),
        "created_logical_clock": created_logical_clock,
        "created_on_server": origin_server,
    }
    return replicated_record(origin_server, origin_sequence, CHANNEL_KIND, created_logical_clock, content)


def publication_record(origin_server: str, origin_sequence: int, channel_name: str, author_username: str) -> dict:
    content = {
        "channel_name": channel_name,
        "author_username": author_username,
        "message": "replicated message",
        "requested_at_ms": current_timestamp_ms(),
        "published_at_ms": current_timestamp_ms(),
        "published_by_server": origin_server,
    }
    return replicated_record(origin_server, origin_sequence, PUBLICATION_KIND, RECORD_LOGICAL_CLOCK, content)
