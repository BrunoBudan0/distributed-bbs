import sqlite3

from errors import ChannelAlreadyExists
from repositories import ChannelRepository


class ChannelController:
    def __init__(self, database_connection: sqlite3.Connection, channel_repository: ChannelRepository) -> None:
        self.database_connection = database_connection
        self.channel_repository = channel_repository

    def create_channel_or_refuse(self, channel_name: str, creator_username: str, created_at_ms: int) -> None:
        with self.database_connection:
            channel_was_created = self.channel_repository.add_if_absent(
                channel_name, creator_username, created_at_ms
            )

        if not channel_was_created:
            raise ChannelAlreadyExists()

    def channel_names(self) -> list[str]:
        return self.channel_repository.all_names()
