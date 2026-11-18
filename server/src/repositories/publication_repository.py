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

    def latest_publications_of(self, channel_name: str, limit: int) -> list[Publication]:
        newest_first_rows = self.database_connection.execute(
            """
            SELECT channel_name, author_username, message, requested_at_ms, published_at_ms, published_by_server
            FROM publication
            WHERE channel_name = ?
            ORDER BY
                published_at_ms DESC,
                published_by_server DESC,
                author_username DESC,
                requested_at_ms DESC,
                message DESC
            LIMIT ?
            """,
            (channel_name, limit),
        ).fetchall()
        return [Publication(*row) for row in reversed(newest_first_rows)]
