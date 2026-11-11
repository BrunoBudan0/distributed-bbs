import sqlite3

from connectors import ChannelPublisher
from errors import ChannelNotFound
from models import Publication
from repositories import ChannelRepository, PublicationRepository


class PublicationController:
    def __init__(
        self,
        database_connection: sqlite3.Connection,
        channel_repository: ChannelRepository,
        publication_repository: PublicationRepository,
        channel_publisher: ChannelPublisher,
    ) -> None:
        self.database_connection = database_connection
        self.channel_repository = channel_repository
        self.publication_repository = publication_repository
        self.channel_publisher = channel_publisher

    def publish_or_refuse(self, publication: Publication) -> None:
        self.refuse_unknown_channel(publication.channel_name)

        with self.database_connection:
            self.publication_repository.add(publication)

        self.channel_publisher.publish(publication)

    def refuse_unknown_channel(self, channel_name: str) -> None:
        if not self.channel_repository.exists(channel_name):
            raise ChannelNotFound()
