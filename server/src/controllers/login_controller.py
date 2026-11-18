import sqlite3

from controllers.replication_log import ReplicationLog
from models import Login, RecordKind
from repositories import LoginRepository


class LoginController:
    def __init__(
        self,
        database_connection: sqlite3.Connection,
        login_repository: LoginRepository,
        replication_log: ReplicationLog,
    ) -> None:
        self.database_connection = database_connection
        self.login_repository = login_repository
        self.replication_log = replication_log

    def record_login(self, login: Login) -> None:
        with self.database_connection:
            self.login_repository.add(login)
            record = self.replication_log.append_local(RecordKind.LOGIN, login)

        self.replication_log.share(record)
