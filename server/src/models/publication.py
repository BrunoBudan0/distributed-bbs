from dataclasses import dataclass


@dataclass(frozen=True)
class Publication:
    channel_name: str
    author_username: str
    message: str
    requested_at_ms: int
    published_at_ms: int
    published_by_server: str
