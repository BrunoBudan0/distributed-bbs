from dataclasses import asdict, dataclass

from constants import REPLICATED_RECORD_OPERATION
from models import ReplicatedRecord


@dataclass(frozen=True)
class ReplicationMessage:
    operation: str
    sender: str
    timestamp: int
    logical_clock: int
    payload: dict

    @classmethod
    def of_record(
        cls, record: ReplicatedRecord, sender_name: str, sent_at_ms: int, logical_clock: int
    ) -> "ReplicationMessage":
        return cls(
            operation=REPLICATED_RECORD_OPERATION,
            sender=sender_name,
            timestamp=sent_at_ms,
            logical_clock=logical_clock,
            payload=record.as_fields(),
        )

    def as_fields(self) -> dict:
        return asdict(self)
