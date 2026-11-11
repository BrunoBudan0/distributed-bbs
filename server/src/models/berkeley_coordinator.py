from dataclasses import dataclass

COORDINATOR_OWN_OFFSET_MS = 0
ALIGNED_OFFSET_MS = 0


@dataclass(frozen=True)
class ClockReading:
    offset_ms: int
    read_at_ms: int


class BerkeleyCoordinator:
    def __init__(self, reading_validity_ms: int) -> None:
        self.reading_validity_ms = reading_validity_ms
        self.readings_by_server: dict[str, ClockReading] = {}

    def offset_of(self, server_name: str) -> int:
        return self.readings_by_server[server_name].offset_ms

    def adjustment_after_reading(self, server_name: str, offset_ms: int, read_at_ms: int) -> int:
        self.readings_by_server[server_name] = ClockReading(offset_ms, read_at_ms)
        self.forget_readings_older_than_validity(read_at_ms)

        fresh_offsets_ms = [COORDINATOR_OWN_OFFSET_MS] + [
            reading.offset_ms for reading in self.readings_by_server.values()
        ]
        adjustment_ms = round(sum(fresh_offsets_ms) / len(fresh_offsets_ms))

        self.move_readings_by(adjustment_ms)
        self.readings_by_server[server_name] = ClockReading(ALIGNED_OFFSET_MS, read_at_ms)
        return adjustment_ms

    def forget_readings_older_than_validity(self, now_ms: int) -> None:
        self.readings_by_server = {
            server_name: reading
            for server_name, reading in self.readings_by_server.items()
            if now_ms - reading.read_at_ms <= self.reading_validity_ms
        }

    def move_readings_by(self, adjustment_ms: int) -> None:
        self.readings_by_server = {
            server_name: ClockReading(reading.offset_ms - adjustment_ms, reading.read_at_ms)
            for server_name, reading in self.readings_by_server.items()
        }
