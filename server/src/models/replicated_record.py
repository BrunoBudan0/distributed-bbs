from dataclasses import dataclass

from constants import CONTENT_FIELD, KIND_FIELD, LOGICAL_CLOCK_FIELD, ORIGIN_SEQUENCE_FIELD, ORIGIN_SERVER_FIELD
from models.channel import Channel
from models.enums import RecordKind
from models.login import Login
from models.publication import Publication

DOMAIN_CLASS_BY_KIND = {RecordKind.LOGIN: Login, RecordKind.CHANNEL: Channel, RecordKind.PUBLICATION: Publication}


@dataclass(frozen=True)
class ReplicatedRecord:
    origin_server: str
    origin_sequence: int
    kind: RecordKind
    logical_clock: int
    content: dict

    def as_fields(self) -> dict:
        return {
            ORIGIN_SERVER_FIELD: self.origin_server,
            ORIGIN_SEQUENCE_FIELD: self.origin_sequence,
            KIND_FIELD: self.kind.value,
            LOGICAL_CLOCK_FIELD: self.logical_clock,
            CONTENT_FIELD: self.content,
        }

    def label(self) -> str:
        return f"{self.origin_server}#{self.origin_sequence}"

    def domain_object(self) -> Login | Channel | Publication:
        return DOMAIN_CLASS_BY_KIND[self.kind](**self.content)
