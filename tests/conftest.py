import os
from collections.abc import Iterator

import pytest

from helpers import BbsClient, ChannelSubscriber, ReferenceClient, ServerDatabase

SATURATES_LOGICAL_CLOCK_MARKER = "saturates_logical_clock"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    items.sort(key=lambda item: item.get_closest_marker(SATURATES_LOGICAL_CLOCK_MARKER) is not None)


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
def reference_client() -> ReferenceClient:
    return ReferenceClient(os.environ["REFERENCE_ENDPOINT"])


@pytest.fixture
def short_timeout_reference_client() -> ReferenceClient:
    return ReferenceClient(os.environ["SHORT_TIMEOUT_REFERENCE_ENDPOINT"])


@pytest.fixture
def short_heartbeat_timeout_ms() -> int:
    return int(os.environ["SHORT_HEARTBEAT_TIMEOUT_MS"])
