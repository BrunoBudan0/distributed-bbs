import sqlite3

from models import Publication


class PublicationRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def add(self, publication: Publication) -> None:
        self.database_connection.execute(
            """
            INSERT INTO publication (
                channel_name, author_username, message, requested_at_ms, published_at_ms, published_by_server
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                publication.channel_name,
                publication.author_username,
                publication.message,
                publication.requested_at_ms,
                publication.published_at_ms,
                publication.published_by_server,
            ),
        )
