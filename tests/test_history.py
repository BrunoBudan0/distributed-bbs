import pytest

from helpers import (
    CHANNEL_HISTORY,
    CHANNEL_HISTORY_LIMIT,
    CHANNEL_NOT_FOUND,
    COORDINATOR_TOPIC,
    INVALID_CHANNEL_NAME,
    REPLICATION_TOPIC,
    TESTED_SERVER_NAME,
    assert_refused,
    assert_succeeded,
    current_timestamp_ms,
    new_channel_name,
    new_created_channel,
    new_ready_channel,
    new_server_name,
    new_username,
    publication_record,
    setup_succeeded,
)

REQUEST_TIMESTAMP_MS = 1762711391123
ONE_MINUTE_MS = 60_000
PUBLICATIONS_BEYOND_THE_LIMIT = 5


def publish_messages_by_one_author(bbs_client, channel_name: str, messages: list[str]) -> None:
    author_username = new_username()
    for message in messages:
        setup_succeeded(bbs_client.publish(channel_name, message, author_username), "publish")


def test_history_lists_the_channel_publications_in_the_order_they_were_published(bbs_client):
    channel_name = new_created_channel(bbs_client)
    publish_messages_by_one_author(bbs_client, channel_name, ["message-1", "message-2", "message-3"])

    response = bbs_client.channel_history(channel_name)

    assert_succeeded(response, CHANNEL_HISTORY)
    assert response["payload"]["channel"] == channel_name
    assert [entry["message"] for entry in response["payload"]["publications"]] == [
        "message-1",
        "message-2",
        "message-3",
    ]


def test_history_entry_matches_the_publication_delivered_live(bbs_client, subscriber):
    channel_name = new_ready_channel(bbs_client, subscriber)
    author_username = new_username()
    setup_succeeded(bbs_client.publish(channel_name, "seen live", author_username, REQUEST_TIMESTAMP_MS), "publish")
    live_publication = subscriber.next_publication()

    history_entries = bbs_client.history_entries(channel_name)

    assert [entry for entry in history_entries if entry["author"] == author_username] == [
        {
            "author": author_username,
            "message": "seen live",
            "timestamp": live_publication.fields["timestamp"],
            "server": TESTED_SERVER_NAME,
        }
    ]


def test_history_keeps_only_the_latest_publications_up_to_the_limit(bbs_client):
    channel_name = new_created_channel(bbs_client)
    published_count = CHANNEL_HISTORY_LIMIT + PUBLICATIONS_BEYOND_THE_LIMIT
    published_messages = [f"message-{order:02d}" for order in range(published_count)]
    publish_messages_by_one_author(bbs_client, channel_name, published_messages)

    assert bbs_client.history_messages(channel_name) == published_messages[-CHANNEL_HISTORY_LIMIT:]


def test_history_of_a_channel_without_publications_is_empty(bbs_client):
    response = bbs_client.channel_history(new_created_channel(bbs_client))

    assert_succeeded(response, CHANNEL_HISTORY)
    assert response["payload"]["publications"] == []


def test_history_leaves_out_publications_of_other_channels(bbs_client):
    channel_name = new_created_channel(bbs_client)
    other_channel_name = new_created_channel(bbs_client)
    publish_messages_by_one_author(bbs_client, other_channel_name, ["elsewhere"])
    publish_messages_by_one_author(bbs_client, channel_name, ["here"])

    assert bbs_client.history_messages(channel_name) == ["here"]


def test_history_includes_publications_replicated_from_another_server(bbs_client, peer_client):
    channel_name = new_created_channel(bbs_client)
    origin_server = new_server_name()
    earlier_publication = publication_record(
        origin_server, 1, channel_name, new_username(), current_timestamp_ms() - ONE_MINUTE_MS
    )
    setup_succeeded(peer_client.push_records([earlier_publication]), "push replicated publication")
    publish_messages_by_one_author(bbs_client, channel_name, ["local message"])

    history_entries = bbs_client.history_entries(channel_name)

    assert [(entry["message"], entry["server"]) for entry in history_entries] == [
        ("replicated message", origin_server),
        ("local message", TESTED_SERVER_NAME),
    ]


def test_history_of_an_unknown_channel_is_refused(bbs_client):
    response = bbs_client.channel_history(new_channel_name())

    assert_refused(response, CHANNEL_NOT_FOUND)
    assert response["operation"] == CHANNEL_HISTORY


@pytest.mark.parametrize(
    "invalid_channel_name",
    ["UPPERCASE", "", None, COORDINATOR_TOPIC, REPLICATION_TOPIC],
    ids=["uppercase", "empty", "null", "servers_topic", "replication_topic"],
)
def test_history_of_a_channel_name_outside_the_format_or_reserved_is_refused(bbs_client, invalid_channel_name):
    assert_refused(bbs_client.channel_history(invalid_channel_name), INVALID_CHANNEL_NAME)
