import os
from collections.abc import Iterator

import pytest

from helpers import BbsClient, ChannelSubscriber, ServerDatabase


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
