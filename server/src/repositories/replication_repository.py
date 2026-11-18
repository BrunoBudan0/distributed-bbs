import json
import sqlite3

from constants import MAX_RECORDS_PER_EXCHANGE, MIN_ORIGIN_SEQUENCE
from models import RecordKind, ReplicatedRecord

NO_RECORDS_WATERMARK = 0


class ReplicationRepository:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection

    def next_sequence_of(self, origin_server: str) -> int:
        highest_sequence = self.database_connection.execute(
            "SELECT MAX(origin_sequence) FROM replicated_record WHERE origin_server = ?", (origin_server,)
        ).fetchone()[0]
        return MIN_ORIGIN_SEQUENCE if highest_sequence is None else highest_sequence + 1

    def add_if_new(self, record: ReplicatedRecord) -> bool:
        inserted_rows = self.database_connection.execute(
            """
            INSERT INTO replicated_record (origin_server, origin_sequence, kind, logical_clock, content)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (origin_server, origin_sequence) DO NOTHING
            """,
            (
                record.origin_server,
                record.origin_sequence,
                record.kind.value,
                record.logical_clock,
                json.dumps(record.content, ensure_ascii=False),
            ),
        )
        return inserted_rows.rowcount == 1

    def contiguous_watermarks(self) -> dict[str, int]:
        rows = self.database_connection.execute(
            """
            SELECT origin_server, COALESCE(MIN(CASE WHEN origin_sequence <> position THEN position - 1 END), MAX(origin_sequence))
            FROM (
                SELECT
                    origin_server,
                    origin_sequence,
                    ROW_NUMBER() OVER (PARTITION BY origin_server ORDER BY origin_sequence) AS position
                FROM replicated_record
            )
            GROUP BY origin_server
            """
        ).fetchall()
        return {origin_server: watermark for origin_server, watermark in rows}

    def records_after(self, watermarks: dict[str, int], limit: int = MAX_RECORDS_PER_EXCHANGE) -> list[ReplicatedRecord]:
        rows = self.database_connection.execute(
            """
            SELECT origin_server, origin_sequence, kind, logical_clock, content
            FROM replicated_record
            ORDER BY origin_server, origin_sequence
            """
        ).fetchall()
        stored_records = [self.record_from_row(stored_row) for stored_row in rows]
        missing_records = [
            record
            for record in stored_records
            if record.origin_sequence > watermarks.get(record.origin_server, NO_RECORDS_WATERMARK)
        ]
        return missing_records[:limit]

    def record_from_row(self, stored_row: tuple) -> ReplicatedRecord:
        origin_server, origin_sequence, kind, logical_clock, content = stored_row
        return ReplicatedRecord(origin_server, origin_sequence, RecordKind(kind), logical_clock, json.loads(content))
