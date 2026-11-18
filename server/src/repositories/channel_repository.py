import sqlite3

from models import Channel


class ChannelRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def add_if_absent(self, channel: Channel) -> bool:
        inserted_rows = self.database_connection.execute(
            """
            INSERT INTO channel (name, created_by_username, created_at_ms, created_logical_clock, created_on_server)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (name) DO NOTHING
            """,
            (
                channel.name,
                channel.created_by_username,
                channel.created_at_ms,
                channel.created_logical_clock,
                channel.created_on_server,
            ),
        )
        return inserted_rows.rowcount == 1

    def replace_creation(self, channel: Channel) -> None:
        self.database_connection.execute(
            """
            UPDATE channel
            SET created_by_username = ?, created_at_ms = ?, created_logical_clock = ?, created_on_server = ?
            WHERE name = ?
            """,
            (
                channel.created_by_username,
                channel.created_at_ms,
                channel.created_logical_clock,
                channel.created_on_server,
                channel.name,
            ),
        )

    def channel_named(self, name: str) -> Channel | None:
        found_row = self.database_connection.execute(
            """
            SELECT name, created_by_username, created_at_ms, created_logical_clock, created_on_server
            FROM channel
            WHERE name = ?
            """,
            (name,),
        ).fetchone()
        return Channel(*found_row) if found_row is not None else None

    def exists(self, name: str) -> bool:
        found_row = self.database_connection.execute("SELECT 1 FROM channel WHERE name = ?", (name,)).fetchone()
        return found_row is not None

    def all_names(self) -> list[str]:
        rows = self.database_connection.execute("SELECT name FROM channel ORDER BY name").fetchall()
        return [channel_name for (channel_name,) in rows]
