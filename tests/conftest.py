import os

import pytest

from helpers import BbsClient, LoginHistory


@pytest.fixture
def bbs_client() -> BbsClient:
    return BbsClient(os.environ["BROKER_CLIENT_ENDPOINT"])


@pytest.fixture
def login_history() -> LoginHistory:
    return LoginHistory(os.environ["SERVER_DATABASE_PATH"])
