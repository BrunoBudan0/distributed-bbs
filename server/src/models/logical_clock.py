from constants import MAX_LOGICAL_CLOCK


class LogicalClock:
    def __init__(self) -> None:
        self.counter = 0

    def tick_for_send(self) -> int:
        self.counter = min(self.counter + 1, MAX_LOGICAL_CLOCK)
        return self.counter

    def observe(self, received_counter: int) -> None:
        self.counter = max(self.counter, received_counter)
