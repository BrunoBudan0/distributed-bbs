import sqlite3
from contextlib import closing


class LoginHistory:
    def __init__(self, database_path: str) -> None:
        self.read_only_uri = f"file:{database_path}?mode=ro"

    def logged_in_timestamps_of(self, username: str) -> list[int]:
        with closing(sqlite3.connect(self.read_only_uri, uri=True)) as database_connection:
            rows = database_connection.execute(
                "SELECT logged_in_at_ms FROM login WHERE username = ? ORDER BY id", (username,)
            ).fetchall()
        return [logged_in_at_ms for (logged_in_at_ms,) in rows]
