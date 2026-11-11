import time

from helpers.assertions import setup_succeeded
from helpers.bbs_client import BbsClient
from helpers.channel_subscriber import ChannelSubscriber, ReceivedPublication
from helpers.names import new_username
from helpers.peer_client import PeerClient
from helpers.protocol import SUCCESS_STATUS
from helpers.waiting import condition_holds_within

ANNOUNCEMENT_WAIT_MS = 300
CLIENT_MESSAGE_ANNOUNCEMENT_WAIT_MS = 50
MAX_ELECTION_ATTEMPTS = 30
COORDINATOR_READY_DEADLINE_MS = 15000


def announcement_after_triggering_elections(
    peer_client: PeerClient, announcement_listener: ChannelSubscriber
) -> ReceivedPublication:
    for _ in range(MAX_ELECTION_ATTEMPTS):
        setup_succeeded(peer_client.request_election(), "election request")
        announcement = announcement_listener.next_publication_within(ANNOUNCEMENT_WAIT_MS)
        if announcement is not None:
            return announcement

    raise AssertionError("no coordinator announcement arrived on the servers topic")


def server_became_coordinator(peer_client: PeerClient) -> bool:
    return condition_holds_within(
        lambda: peer_client.request_clock()["status"] == SUCCESS_STATUS, COORDINATOR_READY_DEADLINE_MS
    )


def announcement_of_coordinator_after_client_messages(
    bbs_client: BbsClient,
    announcement_listener: ChannelSubscriber,
    expected_coordinator_name: str,
    deadline_seconds: float,
) -> ReceivedPublication | None:
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        setup_succeeded(bbs_client.log_in(new_username()), "client message")
        announcement = announcement_listener.next_publication_within(CLIENT_MESSAGE_ANNOUNCEMENT_WAIT_MS)
        if announcement is not None and announcement.fields["payload"].get("coordinator") == expected_coordinator_name:
            return announcement
    return None
