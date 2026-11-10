import sqlite3
from pathlib import Path


def open_database(database_path: Path, schema_path: Path) -> sqlite3.Connection:
    database_connection = sqlite3.connect(database_path)
    database_connection.executescript(schema_path.read_text())
    return database_connection
