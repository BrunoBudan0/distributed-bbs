from helpers.names import new_server_name
from helpers.protocol import HEARTBEAT, LIST_SERVERS, RANK
from helpers.request_exchange import RequestClient


class ReferenceClient(RequestClient):
    def rank(self, server_name: str, logical_clock: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(RANK, server_name, {}, logical_clock=logical_clock))

    def heartbeat(self, server_name: str) -> dict:
        return self.exchange_message(self.valid_request(HEARTBEAT, server_name, {}))

    def list_servers(self) -> dict:
        return self.exchange_message(self.valid_request(LIST_SERVERS, new_server_name(), {}))

    def listed_servers(self) -> list[dict]:
        return self.list_servers()["payload"]["servers"]

    def listed_server_names(self) -> list[str]:
        return [listed_server["name"] for listed_server in self.listed_servers()]
