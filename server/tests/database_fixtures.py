import sqlite3

from constants import SCHEMA_PATH
from database import open_database

IN_MEMORY_DATABASE = ":memory:"


def new_in_memory_database() -> sqlite3.Connection:
    return open_database(IN_MEMORY_DATABASE, SCHEMA_PATH)
