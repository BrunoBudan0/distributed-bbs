from dataclasses import asdict, dataclass

from constants import AUTHOR_FIELD, CHANNEL_FIELD, MESSAGE_FIELD, PUBLICATION_OPERATION
from models import Publication


@dataclass(frozen=True)
class PublicationMessage:
    operation: str
    sender: str
    timestamp: int
    logical_clock: int
    payload: dict

    @classmethod
    def from_publication(cls, publication: Publication, logical_clock: int) -> "PublicationMessage":
        return cls(
            operation=PUBLICATION_OPERATION,
            sender=publication.published_by_server,
            timestamp=publication.published_at_ms,
            logical_clock=logical_clock,
            payload={
                CHANNEL_FIELD: publication.channel_name,
                AUTHOR_FIELD: publication.author_username,
                MESSAGE_FIELD: publication.message,
            },
        )

    def as_fields(self) -> dict:
        return asdict(self)
