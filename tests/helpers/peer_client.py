from helpers.protocol import CLOCK, ELECTION, PEER_TEST_SERVER_NAME
from helpers.request_exchange import RequestClient


class PeerClient(RequestClient):
    def request_election(self, sender: str = PEER_TEST_SERVER_NAME, logical_clock: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(ELECTION, sender, {}, logical_clock=logical_clock))

    def request_clock(self, timestamp: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(CLOCK, PEER_TEST_SERVER_NAME, {}, timestamp))
