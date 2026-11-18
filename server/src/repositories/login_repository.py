import sqlite3

from models import Login


class LoginRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def add(self, login: Login) -> None:
        self.database_connection.execute(
            "INSERT INTO login (username, logged_in_at_ms) VALUES (?, ?)",
            (login.username, login.logged_in_at_ms),
        )

    def logins_of(self, username: str) -> list[Login]:
        rows = self.database_connection.execute(
            "SELECT username, logged_in_at_ms FROM login WHERE username = ? ORDER BY id", (username,)
        ).fetchall()
        return [Login(*row) for row in rows]
