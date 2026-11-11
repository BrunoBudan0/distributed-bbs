from collections.abc import Callable


def cristian_offset_ms(reference_time_ms: int, request_sent_at_ms: int, response_received_at_ms: int) -> int:
    round_trip_ms = response_received_at_ms - request_sent_at_ms
    estimated_reference_time_at_receipt_ms = reference_time_ms + round_trip_ms // 2
    return estimated_reference_time_at_receipt_ms - response_received_at_ms


class PhysicalClock:
    def __init__(self, initial_offset_ms: int, read_system_time_ms: Callable[[], int]) -> None:
        self.offset_ms = initial_offset_ms
        self.read_system_time_ms = read_system_time_ms

    def now_ms(self) -> int:
        return self.read_system_time_ms() + self.offset_ms

    def synchronize(self, reference_time_ms: int, request_sent_at_ms: int, response_received_at_ms: int) -> None:
        self.offset_ms = cristian_offset_ms(reference_time_ms, request_sent_at_ms, response_received_at_ms)
