from uuid import uuid4

import pytest

from helpers import (
    CHANNEL_ALREADY_EXISTS,
    COORDINATOR_TOPIC,
    CREATE_CHANNEL,
    INVALID_CHANNEL_NAME,
    LIST_CHANNELS,
    assert_refused,
    assert_succeeded,
    new_channel_name,
    setup_succeeded,
)

UUID_HEX_LENGTH = 32
SINGLE_CHARACTER_CHANNEL_NAME = "z"


def channel_name_at_maximum_length() -> str:
    channel_name = uuid4().hex
    assert len(channel_name) == UUID_HEX_LENGTH
    return channel_name


def test_created_channel_is_answered_with_success(bbs_client):
    response = bbs_client.create_channel(new_channel_name())

    assert_succeeded(response, CREATE_CHANNEL)
    assert response["payload"] == {}


def test_created_channel_appears_once_in_the_listing(bbs_client):
    channel_name = new_channel_name()

    setup_succeeded(bbs_client.create_channel(channel_name), "create channel")

    assert bbs_client.listed_channel_names().count(channel_name) == 1


def test_channel_name_at_maximum_length_is_created(bbs_client):
    assert_succeeded(bbs_client.create_channel(channel_name_at_maximum_length()), CREATE_CHANNEL)


def test_single_character_channel_name_is_not_refused_as_invalid(bbs_client):
    response = bbs_client.create_channel(SINGLE_CHARACTER_CHANNEL_NAME)

    assert response["payload"].get("error_code") != INVALID_CHANNEL_NAME
    assert SINGLE_CHARACTER_CHANNEL_NAME in bbs_client.listed_channel_names()


def test_duplicate_channel_is_refused_and_stays_listed_once(bbs_client):
    channel_name = new_channel_name()
    setup_succeeded(bbs_client.create_channel(channel_name), "create channel")

    response = bbs_client.create_channel(channel_name)

    assert_refused(response, CHANNEL_ALREADY_EXISTS)
    assert bbs_client.listed_channel_names().count(channel_name) == 1


@pytest.mark.parametrize(
    "invalid_channel_name",
    ["", "UPPERCASE", "with space", "with_underscore", "canção", "a" * 33, "trailing-newline\n", 123, None],
    ids=[
        "empty",
        "uppercase",
        "space",
        "underscore",
        "non_ascii",
        "above_maximum_length",
        "trailing_newline",
        "number",
        "null",
    ],
)
def test_channel_name_outside_the_allowed_format_is_refused_and_not_listed(bbs_client, invalid_channel_name):
    response = bbs_client.create_channel(invalid_channel_name)

    assert_refused(response, INVALID_CHANNEL_NAME)
    assert invalid_channel_name not in bbs_client.listed_channel_names()


def test_channel_named_like_the_coordinator_topic_is_refused(bbs_client):
    response = bbs_client.create_channel(COORDINATOR_TOPIC)

    assert_refused(response, INVALID_CHANNEL_NAME)
    assert COORDINATOR_TOPIC not in bbs_client.listed_channel_names()


def test_listing_contains_only_channel_names(bbs_client):
    setup_succeeded(bbs_client.create_channel(new_channel_name()), "create channel")

    response = bbs_client.list_channels()

    assert_succeeded(response, LIST_CHANNELS)
    assert list(response["payload"]) == ["channels"]
    assert all(type(channel_name) is str for channel_name in response["payload"]["channels"])
