from dataclasses import asdict, dataclass

from constants import COORDINATOR_ANNOUNCEMENT_OPERATION, COORDINATOR_FIELD


@dataclass(frozen=True)
class CoordinatorAnnouncement:
    operation: str
    sender: str
    timestamp: int
    logical_clock: int
    payload: dict

    @classmethod
    def of_coordinator(cls, coordinator_name: str, sent_at_ms: int, logical_clock: int) -> "CoordinatorAnnouncement":
        return cls(
            operation=COORDINATOR_ANNOUNCEMENT_OPERATION,
            sender=coordinator_name,
            timestamp=sent_at_ms,
            logical_clock=logical_clock,
            payload={COORDINATOR_FIELD: coordinator_name},
        )

    def as_fields(self) -> dict:
        return asdict(self)
