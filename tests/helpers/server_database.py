import sqlite3
from contextlib import closing
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredPublication:
    channel_name: str
    author_username: str
    message: str
    requested_at_ms: int
    published_at_ms: int
    published_by_server: str


class ServerDatabase:
    def __init__(self, database_path: str) -> None:
        self.read_only_uri = f"file:{database_path}?mode=ro"

    def logged_in_timestamps_of(self, username: str) -> list[int]:
        rows = self.rows("SELECT logged_in_at_ms FROM login WHERE username = ? ORDER BY id", (username,))
        return [logged_in_at_ms for (logged_in_at_ms,) in rows]

    def publications_of_author(self, author_username: str) -> list[StoredPublication]:
        rows = self.rows(
            """
            SELECT channel_name, author_username, message, requested_at_ms, published_at_ms, published_by_server
            FROM publication
            WHERE author_username = ?
            ORDER BY id
            """,
            (author_username,),
        )
        return [StoredPublication(*row) for row in rows]

    def channel_creation(self, channel_name: str) -> tuple[str, str] | None:
        rows = self.rows(
            "SELECT created_by_username, created_on_server FROM channel WHERE name = ?", (channel_name,)
        )
        return rows[0] if rows else None

    def rows(self, query: str, parameters: tuple) -> list[tuple]:
        with closing(sqlite3.connect(self.read_only_uri, uri=True)) as database_connection:
            return database_connection.execute(query, parameters).fetchall()
