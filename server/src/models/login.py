from dataclasses import dataclass


@dataclass(frozen=True)
class Login:
    username: str
    logged_in_at_ms: int
