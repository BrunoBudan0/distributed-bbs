import sqlite3


class ChannelRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def add_if_absent(self, name: str, created_by_username: str, created_at_ms: int) -> bool:
        inserted_rows = self.database_connection.execute(
            """
            INSERT INTO channel (name, created_by_username, created_at_ms)
            VALUES (?, ?, ?)
            ON CONFLICT (name) DO NOTHING
            """,
            (name, created_by_username, created_at_ms),
        )
        return inserted_rows.rowcount == 1

    def all_names(self) -> list[str]:
        rows = self.database_connection.execute("SELECT name FROM channel ORDER BY name").fetchall()
        return [channel_name for (channel_name,) in rows]
