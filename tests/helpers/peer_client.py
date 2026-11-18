from helpers.protocol import CLOCK, ELECTION, PEER_TEST_SERVER_NAME, REPLICATION_PUSH, REPLICATION_SYNC
from helpers.request_exchange import RequestClient


class PeerClient(RequestClient):
    def request_election(self, sender: str = PEER_TEST_SERVER_NAME, logical_clock: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(ELECTION, sender, {}, logical_clock=logical_clock))

    def request_clock(self, timestamp: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(CLOCK, PEER_TEST_SERVER_NAME, {}, timestamp))

    def request_replication_sync(self, watermarks: object) -> dict:
        return self.exchange_message(
            self.valid_request(REPLICATION_SYNC, PEER_TEST_SERVER_NAME, {"watermarks": watermarks})
        )

    def push_records(self, records: list[dict]) -> dict:
        return self.exchange_message(self.valid_request(REPLICATION_PUSH, PEER_TEST_SERVER_NAME, {"records": records}))
