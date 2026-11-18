import os
from collections.abc import Iterator

import pytest

from helpers import (
    COORDINATOR_TOPIC,
    REPLICATION_TOPIC,
    BbsClient,
    ChannelSubscriber,
    CoordinatorImpersonator,
    PeerClient,
    ReferenceClient,
    ServerDatabase,
)

CHANGES_SHARED_CLOCK_MARKER = "changes_shared_clock"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    items.sort(key=lambda item: item.get_closest_marker(CHANGES_SHARED_CLOCK_MARKER) is not None)


@pytest.fixture
def bbs_client() -> BbsClient:
    return BbsClient(os.environ["BROKER_CLIENT_ENDPOINT"])


@pytest.fixture
def server_database() -> ServerDatabase:
    return ServerDatabase(os.environ["SERVER_DATABASE_PATH"])


@pytest.fixture
def subscriber() -> Iterator[ChannelSubscriber]:
    channel_subscriber = ChannelSubscriber(os.environ["PROXY_SUBSCRIBER_ENDPOINT"])
    yield channel_subscriber
    channel_subscriber.close()


@pytest.fixture
def announcement_listener() -> Iterator[ChannelSubscriber]:
    coordinator_topic_subscriber = ChannelSubscriber(os.environ["PROXY_SUBSCRIBER_ENDPOINT"])
    coordinator_topic_subscriber.subscribe(COORDINATOR_TOPIC)
    yield coordinator_topic_subscriber
    coordinator_topic_subscriber.close()


@pytest.fixture
def replication_listener() -> Iterator[ChannelSubscriber]:
    replication_topic_subscriber = ChannelSubscriber(os.environ["PROXY_SUBSCRIBER_ENDPOINT"])
    replication_topic_subscriber.subscribe(REPLICATION_TOPIC)
    yield replication_topic_subscriber
    replication_topic_subscriber.close()


@pytest.fixture
def coordinator_impersonator() -> Iterator[CoordinatorImpersonator]:
    impersonator = CoordinatorImpersonator(os.environ["PROXY_PUBLISHER_ENDPOINT"])
    yield impersonator
    impersonator.close()


@pytest.fixture
def peer_client() -> PeerClient:
    return PeerClient(os.environ["SERVER_PEER_ENDPOINT"])


@pytest.fixture
def reference_client() -> ReferenceClient:
    return ReferenceClient(os.environ["REFERENCE_ENDPOINT"])


@pytest.fixture
def short_timeout_reference_client() -> ReferenceClient:
    return ReferenceClient(os.environ["SHORT_TIMEOUT_REFERENCE_ENDPOINT"])


@pytest.fixture
def short_heartbeat_timeout_ms() -> int:
    return int(os.environ["SHORT_HEARTBEAT_TIMEOUT_MS"])
