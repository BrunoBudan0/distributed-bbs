import pytest

from helpers import INVALID_USERNAME, LOGIN, assert_refused, assert_succeeded, new_username, setup_succeeded

USERNAME_AT_MAXIMUM_LENGTH = "u" * 32
USERNAME_ABOVE_MAXIMUM_LENGTH = "u" * 33
LOGIN_TIMESTAMP_MS = 1762711391123
SECOND_LOGIN_TIMESTAMP_MS = 1762711399999


def test_login_with_valid_username_succeeds(bbs_client):
    response = bbs_client.log_in(new_username())

    assert_succeeded(response, LOGIN)
    assert response["payload"] == {}


@pytest.mark.parametrize("username", ["a", USERNAME_AT_MAXIMUM_LENGTH, "Bot_1-a"])
def test_usernames_inside_the_allowed_format_are_accepted(bbs_client, username):
    assert_succeeded(bbs_client.log_in(username), LOGIN)


@pytest.mark.parametrize(
    "username",
    ["", USERNAME_ABOVE_MAXIMUM_LENGTH, "name with space", "joão", "name\n"],
    ids=["empty", "above_maximum_length", "space", "non_ascii", "trailing_newline"],
)
def test_username_outside_the_allowed_format_is_refused(bbs_client, username):
    assert_refused(bbs_client.log_in(username), INVALID_USERNAME)


def test_accepted_login_is_stored_on_disk_with_the_message_timestamp(bbs_client, login_history):
    username = new_username()

    setup_succeeded(bbs_client.log_in(username, LOGIN_TIMESTAMP_MS), "login")

    assert login_history.logged_in_timestamps_of(username) == [LOGIN_TIMESTAMP_MS]


def test_every_login_of_the_same_user_is_stored_on_disk(bbs_client, login_history):
    username = new_username()

    setup_succeeded(bbs_client.log_in(username, LOGIN_TIMESTAMP_MS), "first login")
    setup_succeeded(bbs_client.log_in(username, SECOND_LOGIN_TIMESTAMP_MS), "second login")

    assert login_history.logged_in_timestamps_of(username) == [LOGIN_TIMESTAMP_MS, SECOND_LOGIN_TIMESTAMP_MS]


def test_refused_login_stores_nothing_on_disk(bbs_client, login_history):
    refused_username = f"{new_username()} with space"

    assert_refused(bbs_client.log_in(refused_username), INVALID_USERNAME)

    assert login_history.logged_in_timestamps_of(refused_username) == []
