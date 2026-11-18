import sqlite3
from pathlib import Path

from constants import SCHEMA_VERSION
from errors import OutdatedDatabase

EXISTING_TABLES_QUERY = "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"


def open_database(database_path: Path | str, schema_path: Path) -> sqlite3.Connection:
    database_connection = sqlite3.connect(database_path)
    refuse_outdated_schema(database_connection)
    database_connection.executescript(schema_path.read_text())
    database_connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return database_connection


def refuse_outdated_schema(database_connection: sqlite3.Connection) -> None:
    stored_schema_version = database_connection.execute("PRAGMA user_version").fetchone()[0]
    existing_table_count = database_connection.execute(EXISTING_TABLES_QUERY).fetchone()[0]
    if existing_table_count > 0 and stored_schema_version < SCHEMA_VERSION:
        raise OutdatedDatabase(stored_schema_version, SCHEMA_VERSION)
