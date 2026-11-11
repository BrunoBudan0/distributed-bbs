from dataclasses import dataclass

from models import PeerOperation


@dataclass(frozen=True)
class PeerRequestMessage:
    operation: PeerOperation
    sender: str
    timestamp: int
    logical_clock: int
    payload: dict
