from helpers.bbs_client import BbsClient
from helpers.channel_subscriber import ChannelSubscriber, ReceivedPublication
from helpers.publication_scenarios import new_created_channel

RECORD_WAIT_MS = 300
MAX_CHANNEL_ATTEMPTS = 30


def published_record_of_a_new_channel(
    bbs_client: BbsClient, replication_listener: ChannelSubscriber
) -> ReceivedPublication | None:
    for _ in range(MAX_CHANNEL_ATTEMPTS):
        channel_name = new_created_channel(bbs_client)
        published_record = record_about_channel(replication_listener, channel_name)
        if published_record is not None:
            return published_record
    return None


def record_about_channel(replication_listener: ChannelSubscriber, channel_name: str) -> ReceivedPublication | None:
    published_record = replication_listener.next_publication_within(RECORD_WAIT_MS)
    while published_record is not None:
        if published_record.fields["payload"]["content"].get("name") == channel_name:
            return published_record
        published_record = replication_listener.next_publication_within(RECORD_WAIT_MS)
    return None
