from dataclasses import asdict, dataclass

from constants import STATUS_FIELD
from models import ResponseStatus


@dataclass(frozen=True)
class ResponseMessage:
    operation: str
    sender: str
    timestamp: int
    status: ResponseStatus
    payload: dict

    def as_fields(self) -> dict:
        return {**asdict(self), STATUS_FIELD: self.status.value}
