from models import Channel

EARLIER_LOGICAL_CLOCK = 10
LATER_LOGICAL_CLOCK = 20


def channel_created(logical_clock: int, created_on_server: str) -> Channel:
    return Channel(
        name="news",
        created_by_username="bot-1",
        created_at_ms=1_000,
        created_logical_clock=logical_clock,
        created_on_server=created_on_server,
    )


def test_creation_with_the_smaller_logical_clock_wins():
    earlier_creation = channel_created(EARLIER_LOGICAL_CLOCK, "server-2")
    later_creation = channel_created(LATER_LOGICAL_CLOCK, "server-1")

    assert earlier_creation.wins_over(later_creation)
    assert not later_creation.wins_over(earlier_creation)


def test_equal_logical_clocks_are_decided_by_the_server_name():
    creation_on_server_1 = channel_created(EARLIER_LOGICAL_CLOCK, "server-1")
    creation_on_server_2 = channel_created(EARLIER_LOGICAL_CLOCK, "server-2")

    assert creation_on_server_1.wins_over(creation_on_server_2)
    assert not creation_on_server_2.wins_over(creation_on_server_1)
