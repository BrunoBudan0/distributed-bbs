import json
import time

import msgpack
import pytest

from helpers import (
    LOGIN,
    MALFORMED_MESSAGE,
    MAX_TIMESTAMP_MS,
    UNIDENTIFIED_OPERATION,
    UNKNOWN_OPERATION,
    assert_refused,
    assert_succeeded,
    new_username,
)

VALID_TIMESTAMP_MS = 1762711391123
MILLISECONDS_PER_SECOND = 1000
SERVER_NAME = "server-1"


def complete_login_message() -> dict:
    return {"operation": LOGIN, "sender": new_username(), "timestamp": VALID_TIMESTAMP_MS, "payload": {}}


def test_json_bytes_are_refused_as_malformed(bbs_client):
    response = bbs_client.exchange_bytes(json.dumps(complete_login_message()).encode())

    assert_refused(response, MALFORMED_MESSAGE)
    assert response["operation"] == UNIDENTIFIED_OPERATION


def test_truncated_message_pack_is_refused_as_malformed(bbs_client):
    truncated_message = msgpack.packb(complete_login_message())[:-1]

    assert_refused(bbs_client.exchange_bytes(truncated_message), MALFORMED_MESSAGE)


def test_message_pack_that_is_not_a_map_is_refused_as_malformed(bbs_client):
    assert_refused(bbs_client.exchange_message(["login"]), MALFORMED_MESSAGE)


@pytest.mark.parametrize("missing_field", ["operation", "sender", "timestamp", "payload"])
def test_message_without_a_required_field_is_refused_as_malformed(bbs_client, missing_field):
    incomplete_message = complete_login_message()
    del incomplete_message[missing_field]

    assert_refused(bbs_client.exchange_message(incomplete_message), MALFORMED_MESSAGE)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("timestamp", "1762711391123"),
        ("timestamp", True),
        ("timestamp", 1762711391.5),
        ("timestamp", -1),
        ("timestamp", MAX_TIMESTAMP_MS + 1),
        ("sender", 123),
        ("operation", 123),
        ("operation", ["login"]),
        ("payload", []),
    ],
    ids=[
        "timestamp_text",
        "timestamp_boolean",
        "timestamp_float",
        "timestamp_negative",
        "timestamp_above_maximum",
        "sender_number",
        "operation_number",
        "operation_list",
        "payload_list",
    ],
)
def test_field_with_invalid_value_is_refused_as_malformed(bbs_client, field_name, invalid_value):
    invalid_message = {**complete_login_message(), field_name: invalid_value}

    assert_refused(bbs_client.exchange_message(invalid_message), MALFORMED_MESSAGE)


@pytest.mark.parametrize("timestamp", [0, MAX_TIMESTAMP_MS], ids=["minimum", "maximum"])
def test_timestamp_at_the_limits_is_accepted(bbs_client, timestamp):
    assert_succeeded(bbs_client.log_in(new_username(), timestamp), LOGIN)


def test_unknown_operation_is_refused(bbs_client):
    unknown_operation_message = {**complete_login_message(), "operation": "delete_channel"}

    response = bbs_client.exchange_message(unknown_operation_message)

    assert_refused(response, UNKNOWN_OPERATION)
    assert response["operation"] == UNIDENTIFIED_OPERATION


def test_server_keeps_answering_after_a_malformed_message(bbs_client):
    assert_refused(bbs_client.exchange_bytes(b"not message pack bytes"), MALFORMED_MESSAGE)

    assert_succeeded(bbs_client.log_in(new_username()), LOGIN)


def test_response_carries_its_send_timestamp_in_milliseconds(bbs_client):
    earliest_expected_timestamp = int(time.time() * MILLISECONDS_PER_SECOND)

    response = bbs_client.log_in(new_username())

    latest_expected_timestamp = int(time.time() * MILLISECONDS_PER_SECOND)
    assert type(response["timestamp"]) is int
    assert earliest_expected_timestamp <= response["timestamp"] <= latest_expected_timestamp


def test_response_identifies_the_server_that_answered(bbs_client):
    assert bbs_client.log_in(new_username())["sender"] == SERVER_NAME
