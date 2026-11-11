from dataclasses import dataclass

from models import Operation


@dataclass(frozen=True)
class RequestMessage:
    operation: Operation
    sender: str
    timestamp: int
    logical_clock: int
    payload: dict
