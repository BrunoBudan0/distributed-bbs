from dataclasses import dataclass

from constants import AUTHOR_FIELD, CHANNEL_FIELD, MESSAGE_FIELD, PUBLICATIONS_FIELD, SERVER_FIELD, TIMESTAMP_FIELD
from models import Publication


@dataclass(frozen=True)
class ChannelHistory:
    channel_name: str
    publications: list[Publication]

    def as_fields(self) -> dict:
        return {
            CHANNEL_FIELD: self.channel_name,
            PUBLICATIONS_FIELD: [history_entry_of(publication) for publication in self.publications],
        }


def history_entry_of(publication: Publication) -> dict:
    return {
        AUTHOR_FIELD: publication.author_username,
        MESSAGE_FIELD: publication.message,
        TIMESTAMP_FIELD: publication.published_at_ms,
        SERVER_FIELD: publication.published_by_server,
    }
