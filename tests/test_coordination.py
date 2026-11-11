import pytest

from helpers import (
    CLOCK,
    COORDINATOR_ANNOUNCEMENT,
    COORDINATOR_TOPIC,
    ELECTION,
    INVALID_SERVER_NAME,
    MALFORMED_MESSAGE,
    NOT_COORDINATOR,
    PEER_TEST_SERVER_NAME,
    TESTED_SERVER_NAME,
    UNKNOWN_OPERATION,
    announcement_after_triggering_elections,
    announcement_of_coordinator_after_client_messages,
    assert_refused,
    assert_succeeded,
    condition_holds_within,
    current_timestamp_ms,
    server_became_coordinator,
)

CLOCK_SYNCHRONIZATION_TOLERANCE_MS = 300
REQUEST_CLOCK_AHEAD_OF_THE_SERVER = 1_000
IMPERSONATION_DEADLINE_MS = 15000
TAKEOVER_DEADLINE_SECONDS = 30
UNREACHABLE_COORDINATOR_NAME = "server-ghost"
REQUESTER_CLOCK_AHEAD_MS = 10_000


def server_accepted_the_impersonated_coordinator(peer_client, coordinator_impersonator) -> bool:
    coordinator_impersonator.announce(UNREACHABLE_COORDINATOR_NAME)
    return peer_client.request_clock()["payload"].get("error_code") == NOT_COORDINATOR


def test_election_request_is_answered_with_ok(peer_client):
    response = peer_client.request_election()

    assert_succeeded(response, ELECTION)
    assert response["sender"] == TESTED_SERVER_NAME
    assert response["payload"] == {}


def test_election_request_makes_the_highest_ranked_server_announce_itself_on_the_servers_topic(
    peer_client, announcement_listener
):
    announcement = announcement_after_triggering_elections(peer_client, announcement_listener)

    assert announcement.topic == COORDINATOR_TOPIC
    assert announcement.fields["operation"] == COORDINATOR_ANNOUNCEMENT
    assert announcement.fields["sender"] == TESTED_SERVER_NAME
    assert announcement.fields["payload"] == {"coordinator": TESTED_SERVER_NAME}
    assert type(announcement.fields["timestamp"]) is int
    assert type(announcement.fields["logical_clock"]) is int


def test_coordinator_answers_a_clock_request_with_the_correct_time(peer_client):
    assert server_became_coordinator(peer_client)
    earliest_expected_time = current_timestamp_ms() - CLOCK_SYNCHRONIZATION_TOLERANCE_MS

    response = peer_client.request_clock()

    latest_expected_time = current_timestamp_ms() + CLOCK_SYNCHRONIZATION_TOLERANCE_MS
    assert_succeeded(response, CLOCK)
    assert earliest_expected_time <= response["payload"]["time"] <= latest_expected_time


def test_peer_response_carries_the_request_logical_clock_plus_one(peer_client):
    current_server_clock = peer_client.request_election()["logical_clock"]
    request_logical_clock = current_server_clock + REQUEST_CLOCK_AHEAD_OF_THE_SERVER

    response = peer_client.request_election(logical_clock=request_logical_clock)

    assert response["logical_clock"] == request_logical_clock + 1


def test_peer_request_with_an_unknown_operation_is_refused(peer_client):
    message = peer_client.valid_request("login", PEER_TEST_SERVER_NAME, {})

    assert_refused(peer_client.exchange_message(message), UNKNOWN_OPERATION)


def test_peer_request_from_an_invalid_server_name_is_refused(peer_client):
    assert_refused(peer_client.request_election(sender="name with space"), INVALID_SERVER_NAME)


def test_peer_request_that_is_not_message_pack_is_refused(peer_client):
    assert_refused(peer_client.exchange_bytes(b"not message pack bytes"), MALFORMED_MESSAGE)


def test_server_that_learns_of_an_unreachable_coordinator_holds_an_election_and_takes_over(
    peer_client, bbs_client, announcement_listener, coordinator_impersonator
):
    announcement_after_triggering_elections(peer_client, announcement_listener)
    impersonation_was_accepted = condition_holds_within(
        lambda: server_accepted_the_impersonated_coordinator(peer_client, coordinator_impersonator),
        IMPERSONATION_DEADLINE_MS,
    )

    takeover_announcement = announcement_of_coordinator_after_client_messages(
        bbs_client, announcement_listener, TESTED_SERVER_NAME, TAKEOVER_DEADLINE_SECONDS
    )

    assert impersonation_was_accepted
    assert takeover_announcement is not None
    assert_succeeded(peer_client.request_clock(), CLOCK)


@pytest.mark.changes_shared_clock
def test_coordinator_meets_a_clock_that_runs_ahead_halfway(peer_client):
    assert server_became_coordinator(peer_client)
    time_before_request = current_timestamp_ms()

    response = peer_client.request_clock(timestamp=time_before_request + REQUESTER_CLOCK_AHEAD_MS)

    time_after_response = current_timestamp_ms()
    halfway_ms = REQUESTER_CLOCK_AHEAD_MS // 2
    assert_succeeded(response, CLOCK)
    assert (
        time_before_request + halfway_ms - CLOCK_SYNCHRONIZATION_TOLERANCE_MS
        <= response["payload"]["time"]
        <= time_after_response + halfway_ms + CLOCK_SYNCHRONIZATION_TOLERANCE_MS
    )
