from dataclasses import dataclass

from constants import FIRST_RANK
from errors import UnknownServer


@dataclass(frozen=True)
class AvailableServer:
    name: str
    rank: int


class ServerRegistry:
    def __init__(self, heartbeat_timeout_ms: int) -> None:
        self.heartbeat_timeout_ms = heartbeat_timeout_ms
        self.rank_by_name: dict[str, int] = {}
        self.last_contact_ms_by_name: dict[str, int] = {}

    def knows(self, server_name: str) -> bool:
        return server_name in self.rank_by_name

    def rank_of(self, server_name: str, now_ms: int) -> int:
        if not self.knows(server_name):
            self.rank_by_name[server_name] = FIRST_RANK + len(self.rank_by_name)

        self.last_contact_ms_by_name[server_name] = now_ms
        return self.rank_by_name[server_name]

    def record_heartbeat(self, server_name: str, now_ms: int) -> None:
        if not self.knows(server_name):
            raise UnknownServer()

        self.last_contact_ms_by_name[server_name] = now_ms

    def available_servers(self) -> list[AvailableServer]:
        available = [AvailableServer(name, self.rank_by_name[name]) for name in self.last_contact_ms_by_name]
        return sorted(available, key=lambda available_server: available_server.rank)

    def remove_silent_servers(self, now_ms: int) -> list[str]:
        silent_server_names = [
            server_name
            for server_name, last_contact_ms in self.last_contact_ms_by_name.items()
            if now_ms - last_contact_ms > self.heartbeat_timeout_ms
        ]
        for server_name in silent_server_names:
            del self.last_contact_ms_by_name[server_name]
        return silent_server_names
