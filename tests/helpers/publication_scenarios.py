from uuid import uuid4

from helpers.assertions import setup_succeeded
from helpers.bbs_client import BbsClient
from helpers.channel_subscriber import ChannelSubscriber, ReceivedPublication
from helpers.names import new_channel_name

PROBE_WAIT_MS = 200
MAX_PROBE_ATTEMPTS = 50


def new_created_channel(bbs_client: BbsClient) -> str:
    channel_name = new_channel_name()
    setup_succeeded(bbs_client.create_channel(channel_name), "create channel")
    return channel_name


def new_ready_channel(bbs_client: BbsClient, subscriber: ChannelSubscriber) -> str:
    channel_name = new_created_channel(bbs_client)
    subscriber.subscribe(channel_name)
    wait_until_subscription_is_active(bbs_client, subscriber, channel_name)
    return channel_name


def wait_until_subscription_is_active(
    bbs_client: BbsClient, subscriber: ChannelSubscriber, channel_name: str
) -> None:
    for _ in range(MAX_PROBE_ATTEMPTS):
        setup_succeeded(bbs_client.publish(channel_name, f"probe-{uuid4().hex}"), "publish subscription probe")
        if subscriber.next_publication_within(PROBE_WAIT_MS) is not None:
            publications_before_barrier(bbs_client, subscriber, channel_name)
            return

    raise AssertionError(f"the subscription to '{channel_name}' never became active")


def publications_before_barrier(
    bbs_client: BbsClient, subscriber: ChannelSubscriber, channel_name: str
) -> list[ReceivedPublication]:
    barrier_message = f"barrier-{uuid4().hex}"
    setup_succeeded(bbs_client.publish(channel_name, barrier_message), "publish barrier")

    received_before_barrier = []
    while True:
        publication = subscriber.next_publication()
        if publication.message() == barrier_message:
            return received_before_barrier
        received_before_barrier.append(publication)
