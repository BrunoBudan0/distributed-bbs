from models import BerkeleyCoordinator

READING_VALIDITY_MS = 60_000
FIRST_READING_AT_MS = 1_000
SERVER_AHEAD_BY_MS = 7_000
OTHER_SERVER_AHEAD_BY_MS = 3_000
ALIGNED_OFFSET_MS = 0


def test_single_reading_moves_the_coordinator_to_the_average_of_both_clocks():
    berkeley_coordinator = BerkeleyCoordinator(READING_VALIDITY_MS)

    adjustment_ms = berkeley_coordinator.adjustment_after_reading("server-2", SERVER_AHEAD_BY_MS, FIRST_READING_AT_MS)

    assert adjustment_ms == SERVER_AHEAD_BY_MS // 2


def test_average_includes_every_fresh_reading_and_the_coordinator_itself():
    berkeley_coordinator = BerkeleyCoordinator(READING_VALIDITY_MS)
    first_adjustment_ms = berkeley_coordinator.adjustment_after_reading(
        "server-2", ALIGNED_OFFSET_MS, FIRST_READING_AT_MS
    )

    adjustment_ms = berkeley_coordinator.adjustment_after_reading(
        "server-3", OTHER_SERVER_AHEAD_BY_MS, FIRST_READING_AT_MS + 1
    )

    assert first_adjustment_ms == 0
    assert adjustment_ms == OTHER_SERVER_AHEAD_BY_MS // 3


def test_reading_older_than_the_validity_is_left_out_of_the_average():
    berkeley_coordinator = BerkeleyCoordinator(READING_VALIDITY_MS)
    berkeley_coordinator.adjustment_after_reading("server-2", ALIGNED_OFFSET_MS, FIRST_READING_AT_MS)

    adjustment_ms = berkeley_coordinator.adjustment_after_reading(
        "server-3", OTHER_SERVER_AHEAD_BY_MS, FIRST_READING_AT_MS + READING_VALIDITY_MS + 1
    )

    assert adjustment_ms == OTHER_SERVER_AHEAD_BY_MS // 2


def test_requesting_server_counts_as_aligned_after_receiving_the_correct_time():
    berkeley_coordinator = BerkeleyCoordinator(READING_VALIDITY_MS)
    berkeley_coordinator.adjustment_after_reading("server-2", SERVER_AHEAD_BY_MS, FIRST_READING_AT_MS)

    next_adjustment_ms = berkeley_coordinator.adjustment_after_reading("server-2", ALIGNED_OFFSET_MS, FIRST_READING_AT_MS + 1)

    assert next_adjustment_ms == 0


def test_other_readings_follow_the_coordinator_when_it_moves():
    berkeley_coordinator = BerkeleyCoordinator(READING_VALIDITY_MS)
    berkeley_coordinator.adjustment_after_reading("server-2", ALIGNED_OFFSET_MS, FIRST_READING_AT_MS)
    berkeley_coordinator.adjustment_after_reading("server-3", OTHER_SERVER_AHEAD_BY_MS, FIRST_READING_AT_MS + 1)

    assert berkeley_coordinator.offset_of("server-2") == -(OTHER_SERVER_AHEAD_BY_MS // 3)
    assert berkeley_coordinator.offset_of("server-3") == ALIGNED_OFFSET_MS
