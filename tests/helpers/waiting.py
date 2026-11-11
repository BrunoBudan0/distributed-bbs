import time
from collections.abc import Callable

POLL_INTERVAL_SECONDS = 0.2
MILLISECONDS_PER_SECOND = 1000


def condition_holds_within(condition: Callable[[], bool], deadline_ms: int) -> bool:
    deadline = time.monotonic() + deadline_ms / MILLISECONDS_PER_SECOND
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return condition()
