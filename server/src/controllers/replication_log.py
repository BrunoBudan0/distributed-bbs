from dataclasses import asdict

from connectors import ChannelPublisher
from models import Channel, LogicalClock, Login, PhysicalClock, Publication, RecordKind, ReplicatedRecord
from repositories import ReplicationRepository


class ReplicationLog:
    def __init__(
        self,
        server_name: str,
        replication_repository: ReplicationRepository,
        channel_publisher: ChannelPublisher,
        logical_clock: LogicalClock,
        physical_clock: PhysicalClock,
    ) -> None:
        self.server_name = server_name
        self.replication_repository = replication_repository
        self.channel_publisher = channel_publisher
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock

    def append_local(self, kind: RecordKind, domain_object: Login | Channel | Publication) -> ReplicatedRecord:
        record = ReplicatedRecord(
            origin_server=self.server_name,
            origin_sequence=self.replication_repository.next_sequence_of(self.server_name),
            kind=kind,
            logical_clock=self.logical_clock.counter,
            content=asdict(domain_object),
        )
        self.replication_repository.add_if_new(record)
        return record

    def share(self, record: ReplicatedRecord) -> None:
        self.channel_publisher.share_record(record, self.server_name, self.physical_clock.now_ms())
