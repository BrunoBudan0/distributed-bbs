from models import AvailableServer, ServerRegistry
from utils import monotonic_ms, print_registration, print_removal


class ServerRegistryController:
    def __init__(self, server_registry: ServerRegistry) -> None:
        self.server_registry = server_registry

    def rank_for(self, server_name: str) -> int:
        server_is_new = not self.server_registry.knows(server_name)
        rank = self.server_registry.rank_of(server_name, monotonic_ms())
        if server_is_new:
            print_registration(server_name, rank)
        return rank

    def record_heartbeat(self, server_name: str) -> None:
        self.server_registry.record_heartbeat(server_name, monotonic_ms())

    def available_servers(self) -> list[AvailableServer]:
        return self.server_registry.available_servers()

    def remove_silent_servers(self) -> None:
        for server_name in self.server_registry.remove_silent_servers(monotonic_ms()):
            print_removal(server_name, self.server_registry.heartbeat_timeout_ms)
