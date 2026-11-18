import sqlite3

from controllers.replication_log import ReplicationLog
from errors import ChannelAlreadyExists
from models import Channel, RecordKind, ReplicatedRecord
from repositories import ChannelRepository


class ChannelController:
    def __init__(
        self,
        database_connection: sqlite3.Connection,
        channel_repository: ChannelRepository,
        replication_log: ReplicationLog,
    ) -> None:
        self.database_connection = database_connection
        self.channel_repository = channel_repository
        self.replication_log = replication_log

    def create_channel_or_refuse(self, channel: Channel) -> None:
        record = self.recorded_creation_or_refuse(channel)
        self.replication_log.share(record)

    def recorded_creation_or_refuse(self, channel: Channel) -> ReplicatedRecord:
        with self.database_connection:
            if not self.channel_repository.add_if_absent(channel):
                raise ChannelAlreadyExists()
            return self.replication_log.append_local(RecordKind.CHANNEL, channel)

    def channel_names(self) -> list[str]:
        return self.channel_repository.all_names()
