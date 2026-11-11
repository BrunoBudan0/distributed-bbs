from constants import MAX_LOGICAL_CLOCK
from models import LogicalClock, PhysicalClock, cristian_offset_ms

REFERENCE_TIME_MS = 10_000
REQUEST_SENT_AT_MS = 1_000
RESPONSE_RECEIVED_AT_MS = 1_100
HALF_ROUND_TRIP_MS = (RESPONSE_RECEIVED_AT_MS - REQUEST_SENT_AT_MS) // 2
REFERENCE_TIME_AT_THE_MIDDLE_OF_THE_ROUND_TRIP_MS = REQUEST_SENT_AT_MS + HALF_ROUND_TRIP_MS
SIMULATED_SKEW_MS = 7_000
ELAPSED_AFTER_SYNCHRONIZING_MS = 400
LARGER_RECEIVED_LOGICAL_CLOCK = 10
SMALLER_RECEIVED_LOGICAL_CLOCK = 1
SENDS_BEFORE_OBSERVING = 3


class ControlledSystemTime:
    def __init__(self, current_time_ms: int) -> None:
        self.current_time_ms = current_time_ms

    def read(self) -> int:
        return self.current_time_ms


def test_logical_clock_starts_at_zero_and_increments_before_each_send():
    logical_clock = LogicalClock()

    sent_values = [logical_clock.tick_for_send() for _ in range(SENDS_BEFORE_OBSERVING)]

    assert sent_values == [1, 2, 3]


def test_observing_a_larger_logical_clock_adopts_it_and_the_next_send_goes_beyond_it():
    logical_clock = LogicalClock()

    logical_clock.observe(LARGER_RECEIVED_LOGICAL_CLOCK)

    assert logical_clock.tick_for_send() == LARGER_RECEIVED_LOGICAL_CLOCK + 1


def test_observing_a_smaller_logical_clock_keeps_the_current_value():
    logical_clock = LogicalClock()
    for _ in range(SENDS_BEFORE_OBSERVING):
        logical_clock.tick_for_send()

    logical_clock.observe(SMALLER_RECEIVED_LOGICAL_CLOCK)

    assert logical_clock.tick_for_send() == SENDS_BEFORE_OBSERVING + 1


def test_after_observing_the_maximum_the_logical_clock_stays_at_the_maximum_instead_of_going_beyond_it():
    logical_clock = LogicalClock()

    logical_clock.observe(MAX_LOGICAL_CLOCK)

    assert logical_clock.tick_for_send() == MAX_LOGICAL_CLOCK


def test_cristian_offset_adds_half_of_the_round_trip_to_the_reference_time():
    offset_ms = cristian_offset_ms(REFERENCE_TIME_MS, REQUEST_SENT_AT_MS, RESPONSE_RECEIVED_AT_MS)

    assert offset_ms == REFERENCE_TIME_MS + HALF_ROUND_TRIP_MS - RESPONSE_RECEIVED_AT_MS


def test_cristian_offset_is_zero_when_the_clocks_agree():
    offset_ms = cristian_offset_ms(
        REFERENCE_TIME_AT_THE_MIDDLE_OF_THE_ROUND_TRIP_MS, REQUEST_SENT_AT_MS, RESPONSE_RECEIVED_AT_MS
    )

    assert offset_ms == 0


def test_cristian_offset_cancels_a_local_clock_that_runs_ahead():
    offset_ms = cristian_offset_ms(
        REFERENCE_TIME_AT_THE_MIDDLE_OF_THE_ROUND_TRIP_MS,
        REQUEST_SENT_AT_MS + SIMULATED_SKEW_MS,
        RESPONSE_RECEIVED_AT_MS + SIMULATED_SKEW_MS,
    )

    assert offset_ms == -SIMULATED_SKEW_MS


def test_physical_clock_starts_with_the_simulated_skew():
    system_time = ControlledSystemTime(REQUEST_SENT_AT_MS)

    physical_clock = PhysicalClock(SIMULATED_SKEW_MS, system_time.read)

    assert physical_clock.now_ms() == REQUEST_SENT_AT_MS + SIMULATED_SKEW_MS


def test_physical_clock_reads_the_reference_time_after_synchronizing_and_keeps_advancing():
    system_time = ControlledSystemTime(RESPONSE_RECEIVED_AT_MS)
    physical_clock = PhysicalClock(SIMULATED_SKEW_MS, system_time.read)

    physical_clock.synchronize(REFERENCE_TIME_MS, REQUEST_SENT_AT_MS, RESPONSE_RECEIVED_AT_MS)
    time_right_after_synchronizing_ms = physical_clock.now_ms()
    system_time.current_time_ms += ELAPSED_AFTER_SYNCHRONIZING_MS

    assert time_right_after_synchronizing_ms == REFERENCE_TIME_MS + HALF_ROUND_TRIP_MS
    assert physical_clock.now_ms() == REFERENCE_TIME_MS + HALF_ROUND_TRIP_MS + ELAPSED_AFTER_SYNCHRONIZING_MS
