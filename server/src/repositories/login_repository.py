import sqlite3


class LoginRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def add(self, username: str, logged_in_at_ms: int) -> None:
        self.database_connection.execute(
            "INSERT INTO login (username, logged_in_at_ms) VALUES (?, ?)",
            (username, logged_in_at_ms),
        )
