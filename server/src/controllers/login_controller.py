import sqlite3

from repositories import LoginRepository


class LoginController:
    def __init__(self, database_connection: sqlite3.Connection, login_repository: LoginRepository) -> None:
        self.database_connection = database_connection
        self.login_repository = login_repository

    def record_login(self, username: str, logged_in_at_ms: int) -> None:
        with self.database_connection:
            self.login_repository.add(username, logged_in_at_ms)
