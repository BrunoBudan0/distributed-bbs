import pytest

from helpers import (
    CHANNEL_NOT_FOUND,
    INVALID_CHANNEL_NAME,
    INVALID_MESSAGE,
    MAX_MESSAGE_LENGTH,
    PUBLICATION,
    PUBLISH,
    TESTED_SERVER_NAME,
    StoredPublication,
    assert_refused,
    assert_succeeded,
    current_timestamp_ms,
    new_channel_name,
    new_created_channel,
    new_ready_channel,
    new_username,
    publications_before_barrier,
    setup_succeeded,
)

MESSAGE_AT_MAXIMUM_LENGTH = "m" * MAX_MESSAGE_LENGTH
MESSAGE_ABOVE_MAXIMUM_LENGTH = "m" * (MAX_MESSAGE_LENGTH + 1)
REQUEST_TIMESTAMP_MS = 1762711391123
CLOCK_SYNCHRONIZATION_TOLERANCE_MS = 100


def test_publication_in_existing_channel_is_answered_with_success(bbs_client):
    response = bbs_client.publish(new_created_channel(bbs_client), "hello channel")

    assert_succeeded(response, PUBLISH)
    assert response["payload"] == {}


def test_subscriber_receives_the_publication_on_the_channel_topic(bbs_client, subscriber):
    channel_name = new_ready_channel(bbs_client, subscriber)
    author_username = new_username()

    setup_succeeded(bbs_client.publish(channel_name, "hello channel", author_username), "publish")

    publication = subscriber.next_publication()
    assert publication.topic == channel_name
    assert publication.fields["operation"] == PUBLICATION
    assert publication.fields["sender"] == TESTED_SERVER_NAME
    assert publication.fields["payload"] == {
        "channel": channel_name,
        "author": author_username,
        "message": "hello channel",
    }


def test_publication_carries_its_own_send_timestamp_instead_of_the_request_timestamp(bbs_client, subscriber):
    channel_name = new_ready_channel(bbs_client, subscriber)
    earliest_expected_timestamp = current_timestamp_ms()

    setup_succeeded(bbs_client.publish(channel_name, "timed message", timestamp=REQUEST_TIMESTAMP_MS), "publish")

    publication = subscriber.next_publication()
    assert type(publication.fields["timestamp"]) is int
    assert (
        earliest_expected_timestamp - CLOCK_SYNCHRONIZATION_TOLERANCE_MS
        <= publication.fields["timestamp"]
        <= publication.received_at_ms + CLOCK_SYNCHRONIZATION_TOLERANCE_MS
    )


@pytest.mark.parametrize(
    "message",
    ["m", MESSAGE_AT_MAXIMUM_LENGTH, "Olá, canção!\nSegunda linha"],
    ids=["single_character", "maximum_length", "accents_and_line_break"],
)
def test_message_inside_the_allowed_format_is_delivered_unchanged(bbs_client, subscriber, message):
    channel_name = new_ready_channel(bbs_client, subscriber)

    setup_succeeded(bbs_client.publish(channel_name, message), "publish")

    assert subscriber.next_publication().message() == message


def test_accepted_publication_is_stored_on_disk_with_every_field(bbs_client, subscriber, server_database):
    channel_name = new_ready_channel(bbs_client, subscriber)
    author_username = new_username()

    setup_succeeded(bbs_client.publish(channel_name, "stored message", author_username, REQUEST_TIMESTAMP_MS), "publish")

    published_timestamp = subscriber.next_publication().fields["timestamp"]
    assert server_database.publications_of_author(author_username) == [
        StoredPublication(
            channel_name=channel_name,
            author_username=author_username,
            message="stored message",
            requested_at_ms=REQUEST_TIMESTAMP_MS,
            published_at_ms=published_timestamp,
            published_by_server=TESTED_SERVER_NAME,
        )
    ]


def test_publication_in_unknown_channel_is_refused_and_neither_stored_nor_delivered(
    bbs_client, subscriber, server_database
):
    unknown_channel_name = new_channel_name()
    subscriber.subscribe(unknown_channel_name)
    control_channel_name = new_ready_channel(bbs_client, subscriber)
    author_username = new_username()

    response = bbs_client.publish(unknown_channel_name, "lost message", author_username)

    assert_refused(response, CHANNEL_NOT_FOUND)
    assert publications_before_barrier(bbs_client, subscriber, control_channel_name) == []
    assert server_database.publications_of_author(author_username) == []


@pytest.mark.parametrize(
    "invalid_message",
    ["", MESSAGE_ABOVE_MAXIMUM_LENGTH, 123, None],
    ids=["empty", "above_maximum_length", "number", "null"],
)
def test_message_outside_the_allowed_format_is_refused_and_neither_stored_nor_delivered(
    bbs_client, subscriber, server_database, invalid_message
):
    channel_name = new_ready_channel(bbs_client, subscriber)
    author_username = new_username()

    response = bbs_client.publish(channel_name, invalid_message, author_username)

    assert_refused(response, INVALID_MESSAGE)
    assert publications_before_barrier(bbs_client, subscriber, channel_name) == []
    assert server_database.publications_of_author(author_username) == []


@pytest.mark.parametrize("invalid_channel_name", ["UPPERCASE", "", None], ids=["uppercase", "empty", "null"])
def test_channel_name_outside_the_allowed_format_is_refused_for_publication(bbs_client, invalid_channel_name):
    assert_refused(bbs_client.publish(invalid_channel_name, "hello"), INVALID_CHANNEL_NAME)


def test_subscriber_of_one_channel_does_not_receive_publications_of_another(bbs_client, subscriber):
    subscribed_channel_name = new_ready_channel(bbs_client, subscriber)
    other_channel_name = new_created_channel(bbs_client)

    setup_succeeded(bbs_client.publish(other_channel_name, "not for this subscriber"), "publish in other channel")

    assert publications_before_barrier(bbs_client, subscriber, subscribed_channel_name) == []
