import pytest

from helpers import (
    INVALID_RECORD,
    MALFORMED_MESSAGE,
    MAX_LOGICAL_CLOCK,
    REPLICATED_RECORD,
    REPLICATION_PUSH,
    REPLICATION_SYNC,
    TESTED_SERVER_NAME,
    assert_refused,
    assert_succeeded,
    channel_record,
    login_record,
    new_channel_name,
    new_created_channel,
    new_server_name,
    new_username,
    publication_record,
    setup_succeeded,
)
from helpers.replication_scenarios import published_record_of_a_new_channel

LOWEST_LOGICAL_CLOCK = 0


def server_records_after_current_watermark(peer_client, write_through_client) -> list[dict]:
    watermark = setup_succeeded(peer_client.request_replication_sync({}), "first sync")["payload"]["watermarks"].get(
        TESTED_SERVER_NAME, 0
    )
    write_through_client()
    response = setup_succeeded(peer_client.request_replication_sync({TESTED_SERVER_NAME: watermark}), "second sync")
    return [record for record in response["payload"]["records"] if record["origin_server"] == TESTED_SERVER_NAME]


def records_of_origin(peer_client, origin_server: str) -> list[dict]:
    response = setup_succeeded(peer_client.request_replication_sync({}), "sync")
    return [record for record in response["payload"]["records"] if record["origin_server"] == origin_server]


def watermark_of(peer_client, origin_server: str) -> int:
    response = setup_succeeded(peer_client.request_replication_sync({}), "sync")
    return response["payload"]["watermarks"].get(origin_server, 0)


def test_channel_created_through_a_client_becomes_the_next_record_of_the_server(bbs_client, peer_client):
    created_channel_names = []

    records = server_records_after_current_watermark(
        peer_client, lambda: created_channel_names.append(new_created_channel(bbs_client))
    )

    assert len(records) == 1
    assert records[0]["kind"] == "channel"
    assert records[0]["content"]["name"] == created_channel_names[0]
    assert records[0]["content"]["created_on_server"] == TESTED_SERVER_NAME


def test_login_through_a_client_becomes_a_record_with_its_timestamp(bbs_client, peer_client):
    username = new_username()

    records = server_records_after_current_watermark(
        peer_client, lambda: setup_succeeded(bbs_client.log_in(username, timestamp=1_762_711_391_123), "login")
    )

    assert [record["content"] for record in records] == [{"username": username, "logged_in_at_ms": 1_762_711_391_123}]


def test_publication_through_a_client_becomes_a_record_with_every_field(bbs_client, peer_client):
    channel_name = new_created_channel(bbs_client)
    author_username = new_username()

    records = server_records_after_current_watermark(
        peer_client,
        lambda: setup_succeeded(bbs_client.publish(channel_name, "replicated hello", author_username), "publish"),
    )

    assert len(records) == 1
    assert records[0]["kind"] == "publication"
    assert records[0]["content"]["channel_name"] == channel_name
    assert records[0]["content"]["author_username"] == author_username
    assert records[0]["content"]["message"] == "replicated hello"
    assert records[0]["content"]["published_by_server"] == TESTED_SERVER_NAME


def test_pushed_channel_record_is_listed_to_clients(bbs_client, peer_client):
    channel_name = new_channel_name()

    response = peer_client.push_records([channel_record(new_server_name(), 1, channel_name, LOWEST_LOGICAL_CLOCK)])

    assert_succeeded(response, REPLICATION_PUSH)
    assert channel_name in bbs_client.listed_channel_names()


def test_record_pushed_twice_is_kept_once(bbs_client, peer_client):
    origin_server = new_server_name()
    record = channel_record(origin_server, 1, new_channel_name(), LOWEST_LOGICAL_CLOCK)

    setup_succeeded(peer_client.push_records([record]), "first push")
    setup_succeeded(peer_client.push_records([record]), "second push")

    assert bbs_client.listed_channel_names().count(record["content"]["name"]) == 1
    assert len(records_of_origin(peer_client, origin_server)) == 1


def test_watermark_stops_before_a_missing_sequence_and_moves_when_it_arrives(peer_client):
    origin_server = new_server_name()

    setup_succeeded(peer_client.push_records([login_record(origin_server, 2, new_username())]), "push second")
    watermark_with_gap = watermark_of(peer_client, origin_server)
    setup_succeeded(peer_client.push_records([login_record(origin_server, 1, new_username())]), "push first")

    assert watermark_with_gap == 0
    assert watermark_of(peer_client, origin_server) == 2


def test_concurrent_creation_with_a_smaller_logical_clock_takes_over_the_channel(
    bbs_client, peer_client, server_database
):
    channel_name = new_created_channel(bbs_client)
    origin_server = new_server_name()

    setup_succeeded(
        peer_client.push_records([channel_record(origin_server, 1, channel_name, LOWEST_LOGICAL_CLOCK)]), "push"
    )

    assert server_database.channel_creation(channel_name)[1] == origin_server
    assert bbs_client.listed_channel_names().count(channel_name) == 1


def test_concurrent_creation_with_a_larger_logical_clock_leaves_the_channel_as_it_was(
    bbs_client, peer_client, server_database
):
    channel_name = new_created_channel(bbs_client)

    setup_succeeded(
        peer_client.push_records([channel_record(new_server_name(), 1, channel_name, MAX_LOGICAL_CLOCK)]), "push"
    )

    assert server_database.channel_creation(channel_name)[1] == TESTED_SERVER_NAME


def test_publication_record_for_a_channel_the_server_does_not_know_yet_is_kept(peer_client, server_database):
    author_username = new_username()
    record = publication_record(new_server_name(), 1, new_channel_name(), author_username)

    response = peer_client.push_records([record])

    assert_succeeded(response, REPLICATION_PUSH)
    assert len(server_database.publications_of_author(author_username)) == 1


@pytest.mark.parametrize(
    "invalid_change",
    [
        {"kind": "message"},
        {"origin_sequence": 0},
        {"origin_server": "name with space"},
        {"content": {"name": "UPPERCASE"}},
    ],
    ids=["unknown_kind", "sequence_zero", "invalid_origin", "invalid_content"],
)
def test_record_outside_the_protocol_is_refused_and_nothing_is_kept(bbs_client, peer_client, invalid_change):
    origin_server = new_server_name()
    record = {**channel_record(origin_server, 1, new_channel_name(), LOWEST_LOGICAL_CLOCK), **invalid_change}

    response = peer_client.push_records([record])

    assert_refused(response, INVALID_RECORD)
    assert records_of_origin(peer_client, origin_server) == []


def test_synchronization_with_malformed_watermarks_is_refused(peer_client):
    response = peer_client.request_replication_sync({TESTED_SERVER_NAME: "not a number"})

    assert_refused(response, MALFORMED_MESSAGE)
    assert response["operation"] == REPLICATION_SYNC


def test_every_write_is_published_on_the_replication_topic(bbs_client, replication_listener):
    published_record = published_record_of_a_new_channel(bbs_client, replication_listener)

    assert published_record is not None
    assert published_record.fields["operation"] == REPLICATED_RECORD
    assert published_record.fields["sender"] == TESTED_SERVER_NAME
    assert published_record.fields["payload"]["origin_server"] == TESTED_SERVER_NAME
    assert published_record.fields["payload"]["kind"] == "channel"
