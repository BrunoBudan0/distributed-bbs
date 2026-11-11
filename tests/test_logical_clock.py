from helpers import (
    INVALID_USERNAME,
    LOGIN,
    assert_refused,
    assert_succeeded,
    new_ready_channel,
    new_username,
    setup_succeeded,
)

REQUEST_LOGICAL_CLOCK = 1_000_000
HIGHER_REQUEST_LOGICAL_CLOCK = 5_000_000
PUBLICATION_REQUEST_LOGICAL_CLOCK = 7_000_000
REFUSED_REQUEST_LOGICAL_CLOCK = 9_000_000
LOWEST_LOGICAL_CLOCK = 1


def test_response_logical_clock_is_greater_than_the_request_logical_clock(bbs_client):
    response = bbs_client.log_in(new_username(), logical_clock=REQUEST_LOGICAL_CLOCK)

    assert_succeeded(response, LOGIN)
    assert type(response["logical_clock"]) is int
    assert response["logical_clock"] > REQUEST_LOGICAL_CLOCK


def test_server_logical_clock_never_goes_back_after_a_request_with_a_smaller_clock(bbs_client):
    setup_succeeded(bbs_client.log_in(new_username(), logical_clock=HIGHER_REQUEST_LOGICAL_CLOCK), "login")

    response = bbs_client.log_in(new_username(), logical_clock=LOWEST_LOGICAL_CLOCK)

    assert response["logical_clock"] > HIGHER_REQUEST_LOGICAL_CLOCK


def test_consecutive_responses_carry_increasing_logical_clocks(bbs_client):
    first_response = bbs_client.log_in(new_username(), logical_clock=LOWEST_LOGICAL_CLOCK)
    second_response = bbs_client.log_in(new_username(), logical_clock=LOWEST_LOGICAL_CLOCK)

    assert second_response["logical_clock"] > first_response["logical_clock"]


def test_publication_logical_clock_lies_between_the_request_and_the_response(bbs_client, subscriber):
    channel_name = new_ready_channel(bbs_client, subscriber)

    response = bbs_client.publish(channel_name, "clocked message", logical_clock=PUBLICATION_REQUEST_LOGICAL_CLOCK)

    publication = subscriber.next_publication()
    assert PUBLICATION_REQUEST_LOGICAL_CLOCK < publication.fields["logical_clock"] < response["logical_clock"]


def test_refusal_also_carries_a_logical_clock_greater_than_the_request(bbs_client):
    response = bbs_client.log_in("name with space", logical_clock=REFUSED_REQUEST_LOGICAL_CLOCK)

    assert_refused(response, INVALID_USERNAME)
    assert response["logical_clock"] > REFUSED_REQUEST_LOGICAL_CLOCK
