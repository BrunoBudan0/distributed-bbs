from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    name: str
    created_by_username: str
    created_at_ms: int
    created_logical_clock: int
    created_on_server: str

    def wins_over(self, other_creation: "Channel") -> bool:
        return (self.created_logical_clock, self.created_on_server) < (
            other_creation.created_logical_clock,
            other_creation.created_on_server,
        )
