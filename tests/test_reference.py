import time

import msgpack
import pytest

from helpers import (
    HEARTBEAT,
    INVALID_SERVER_NAME,
    LIST_SERVERS,
    MALFORMED_MESSAGE,
    MAX_LOGICAL_CLOCK,
    RANK,
    REFERENCE_NAME,
    TESTED_SERVER_NAME,
    UNKNOWN_OPERATION,
    UNKNOWN_SERVER,
    assert_refused,
    assert_succeeded,
    condition_holds_within,
    new_server_name,
    setup_succeeded,
)

REQUEST_LOGICAL_CLOCK = 1_000_000
REQUEST_CLOCK_AHEAD_OF_THE_REFERENCE = 1_000
REMOVAL_DEADLINE_FACTOR = 5
REGISTRATION_DEADLINE_MS = 10000
HEARTBEATS_PER_TIMEOUT = 3
OBSERVED_TIMEOUTS = 2
MILLISECONDS_PER_SECOND = 1000
SERVER_NAME_ABOVE_MAXIMUM_LENGTH = "s" * 33


def registered_rank(reference_client, server_name: str) -> int:
    return setup_succeeded(reference_client.rank(server_name), "rank request")["payload"]["rank"]


def test_first_rank_request_receives_a_positive_integer_rank(short_timeout_reference_client):
    response = short_timeout_reference_client.rank(new_server_name())

    assert_succeeded(response, RANK)
    assert type(response["payload"]["rank"]) is int
    assert response["payload"]["rank"] >= 1


def test_same_server_name_always_receives_the_same_rank(short_timeout_reference_client):
    server_name = new_server_name()
    first_rank = registered_rank(short_timeout_reference_client, server_name)

    second_rank = registered_rank(short_timeout_reference_client, server_name)

    assert second_rank == first_rank


def test_different_server_names_receive_increasing_ranks(short_timeout_reference_client):
    first_rank = registered_rank(short_timeout_reference_client, new_server_name())

    second_rank = registered_rank(short_timeout_reference_client, new_server_name())

    assert second_rank > first_rank


def test_registered_server_is_listed_once_with_its_name_and_rank(short_timeout_reference_client):
    server_name = new_server_name()
    rank = registered_rank(short_timeout_reference_client, server_name)

    response = short_timeout_reference_client.list_servers()

    assert_succeeded(response, LIST_SERVERS)
    assert response["payload"]["servers"].count({"name": server_name, "rank": rank}) == 1


def test_server_list_is_ordered_by_rank(short_timeout_reference_client):
    registered_rank(short_timeout_reference_client, new_server_name())
    registered_rank(short_timeout_reference_client, new_server_name())

    listed_ranks = [listed_server["rank"] for listed_server in short_timeout_reference_client.listed_servers()]

    assert listed_ranks == sorted(listed_ranks)


def test_heartbeat_of_a_registered_server_is_answered_with_ok_and_no_time(short_timeout_reference_client):
    server_name = new_server_name()
    registered_rank(short_timeout_reference_client, server_name)

    response = short_timeout_reference_client.heartbeat(server_name)

    assert_succeeded(response, HEARTBEAT)
    assert response["payload"] == {}


def test_heartbeat_of_a_server_that_never_asked_for_a_rank_is_refused_and_not_listed(short_timeout_reference_client):
    server_name = new_server_name()

    response = short_timeout_reference_client.heartbeat(server_name)

    assert_refused(response, UNKNOWN_SERVER)
    assert server_name not in short_timeout_reference_client.listed_server_names()


def test_silent_server_leaves_the_list_and_returns_with_the_same_rank_after_a_heartbeat(
    short_timeout_reference_client, short_heartbeat_timeout_ms
):
    server_name = new_server_name()
    rank = registered_rank(short_timeout_reference_client, server_name)
    assert server_name in short_timeout_reference_client.listed_server_names()

    server_was_removed = condition_holds_within(
        lambda: server_name not in short_timeout_reference_client.listed_server_names(),
        short_heartbeat_timeout_ms * REMOVAL_DEADLINE_FACTOR,
    )

    assert server_was_removed
    assert_succeeded(short_timeout_reference_client.heartbeat(server_name), HEARTBEAT)
    assert {"name": server_name, "rank": rank} in short_timeout_reference_client.listed_servers()


def listing_after_each_regular_heartbeat(reference_client, server_name: str, heartbeat_timeout_ms: int) -> list[bool]:
    heartbeat_interval_seconds = heartbeat_timeout_ms / HEARTBEATS_PER_TIMEOUT / MILLISECONDS_PER_SECOND
    observation_end = time.monotonic() + heartbeat_timeout_ms * OBSERVED_TIMEOUTS / MILLISECONDS_PER_SECOND
    listing_after_each_heartbeat = []
    while time.monotonic() < observation_end:
        setup_succeeded(reference_client.heartbeat(server_name), "regular heartbeat")
        listing_after_each_heartbeat.append(server_name in reference_client.listed_server_names())
        time.sleep(heartbeat_interval_seconds)
    return listing_after_each_heartbeat


def test_server_with_regular_heartbeats_stays_listed_beyond_the_timeout(
    short_timeout_reference_client, short_heartbeat_timeout_ms
):
    server_name = new_server_name()
    registered_rank(short_timeout_reference_client, server_name)

    listing_after_each_heartbeat = listing_after_each_regular_heartbeat(
        short_timeout_reference_client, server_name, short_heartbeat_timeout_ms
    )

    assert len(listing_after_each_heartbeat) > HEARTBEATS_PER_TIMEOUT
    assert all(listing_after_each_heartbeat)


@pytest.mark.parametrize(
    "invalid_server_name",
    ["", "name with space", SERVER_NAME_ABOVE_MAXIMUM_LENGTH],
    ids=["empty", "space", "above_maximum_length"],
)
def test_server_name_outside_the_allowed_format_is_refused(short_timeout_reference_client, invalid_server_name):
    assert_refused(short_timeout_reference_client.rank(invalid_server_name), INVALID_SERVER_NAME)


def test_unknown_operation_is_refused_by_the_reference(short_timeout_reference_client):
    message = short_timeout_reference_client.valid_request("publish", new_server_name(), {})

    assert_refused(short_timeout_reference_client.exchange_message(message), UNKNOWN_OPERATION)


def test_bytes_that_are_not_message_pack_are_refused_by_the_reference(short_timeout_reference_client):
    assert_refused(short_timeout_reference_client.exchange_bytes(b"not message pack bytes"), MALFORMED_MESSAGE)


def test_message_without_logical_clock_is_refused_by_the_reference(short_timeout_reference_client):
    message = short_timeout_reference_client.valid_request(RANK, new_server_name(), {})
    del message["logical_clock"]

    assert_refused(short_timeout_reference_client.exchange_bytes(msgpack.packb(message)), MALFORMED_MESSAGE)


@pytest.mark.changes_shared_clock
def test_logical_clock_at_the_maximum_is_accepted_and_does_not_stop_later_requests(short_timeout_reference_client):
    response_to_maximum = short_timeout_reference_client.rank(new_server_name(), logical_clock=MAX_LOGICAL_CLOCK)

    response_to_next_request = short_timeout_reference_client.rank(new_server_name())

    assert_succeeded(response_to_maximum, RANK)
    assert response_to_maximum["logical_clock"] == MAX_LOGICAL_CLOCK
    assert_succeeded(response_to_next_request, RANK)


def test_reference_refusal_also_carries_a_logical_clock_greater_than_the_request(short_timeout_reference_client):
    response = short_timeout_reference_client.rank("name with space", logical_clock=REQUEST_LOGICAL_CLOCK)

    assert_refused(response, INVALID_SERVER_NAME)
    assert response["logical_clock"] > REQUEST_LOGICAL_CLOCK


def test_reference_response_identifies_the_reference_and_carries_the_request_clock_plus_one(
    short_timeout_reference_client,
):
    current_reference_clock = short_timeout_reference_client.rank(new_server_name())["logical_clock"]
    request_logical_clock = current_reference_clock + REQUEST_CLOCK_AHEAD_OF_THE_REFERENCE

    response = short_timeout_reference_client.rank(new_server_name(), logical_clock=request_logical_clock)

    assert response["sender"] == REFERENCE_NAME
    assert response["logical_clock"] == request_logical_clock + 1


def test_running_server_registers_itself_in_the_reference(reference_client):
    server_is_listed = condition_holds_within(
        lambda: TESTED_SERVER_NAME in reference_client.listed_server_names(),
        REGISTRATION_DEADLINE_MS,
    )

    assert server_is_listed
