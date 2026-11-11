from errors import PeerUnavailable
from utils import system_time_ms

ELECTION = "election"
CLOCK = "clock"
NAME_FIELD = "name"
RANK_FIELD = "rank"


def success_response(payload: dict) -> dict:
    return {"status": "success", "logical_clock": 1, "payload": payload}


def error_response(error_code: str) -> dict:
    return {"status": "error", "logical_clock": 1, "payload": {"error_code": error_code}}


class FakeReferenceController:
    def __init__(self, rank: int | None, available_servers: list[dict]) -> None:
        self.rank = rank
        self.available_servers = available_servers

    def refresh_available_servers_or_report_timeout(self) -> None:
        return None

    def rank_of(self, server_name: str) -> int | None:
        for available_server in self.available_servers:
            if available_server[NAME_FIELD] == server_name:
                return available_server[RANK_FIELD]
        return None


class RecordingPeerConnector:
    def __init__(self, unavailable_peer_names: tuple[str, ...] = (), clock_response: dict | None = None) -> None:
        self.unavailable_peer_names = unavailable_peer_names
        self.clock_response = clock_response
        self.requests: list[tuple[str, str]] = []

    def request_election(self, peer_name: str) -> dict:
        self.record_or_fail(peer_name, ELECTION)
        return success_response({})

    def request_clock(self, peer_name: str) -> dict:
        self.record_or_fail(peer_name, CLOCK)
        if self.clock_response is not None:
            return self.clock_response
        return success_response({"time": system_time_ms()})

    def record_or_fail(self, peer_name: str, operation: str) -> None:
        self.requests.append((peer_name, operation))
        if peer_name in self.unavailable_peer_names:
            raise PeerUnavailable(peer_name)


class RecordingChannelPublisher:
    def __init__(self) -> None:
        self.announced_coordinators: list[str] = []

    def announce_coordinator(self, coordinator_name: str, sent_at_ms: int) -> None:
        self.announced_coordinators.append(coordinator_name)


def available_server(name: str, rank: int) -> dict:
    return {NAME_FIELD: name, RANK_FIELD: rank}
