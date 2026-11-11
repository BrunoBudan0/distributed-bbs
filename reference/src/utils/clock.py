import time

NANOSECONDS_PER_MILLISECOND = 1_000_000


def current_timestamp_ms() -> int:
    return time.time_ns() // NANOSECONDS_PER_MILLISECOND


def monotonic_ms() -> int:
    return time.monotonic_ns() // NANOSECONDS_PER_MILLISECOND
