from connectors import ReferenceConnector
from constants import (
    CLIENT_MESSAGES_PER_HEARTBEAT,
    ERROR_CODE_FIELD,
    NAME_FIELD,
    PAYLOAD_FIELD,
    RANK_FIELD,
    SERVERS_FIELD,
    STATUS_FIELD,
    UNKNOWN_SERVER_ERROR_CODE,
)
from errors import ReferenceTimeout
from models import ResponseStatus
from utils import print_available_servers, print_rank, print_unavailable


class ReferenceController:
    def __init__(self, reference_connector: ReferenceConnector) -> None:
        self.reference_connector = reference_connector
        self.rank: int | None = None
        self.available_servers: list[dict] = []
        self.received_client_messages = 0

    def register_or_report_timeout(self) -> None:
        try:
            self.register()
        except ReferenceTimeout as reference_timeout:
            print_unavailable(reference_timeout)

    def refresh_available_servers_or_report_timeout(self) -> None:
        try:
            self.refresh_available_servers()
        except ReferenceTimeout as reference_timeout:
            print_unavailable(reference_timeout)

    def count_client_message(self) -> None:
        self.received_client_messages += 1
        if self.received_client_messages % CLIENT_MESSAGES_PER_HEARTBEAT == 0:
            self.heartbeat_or_report_timeout()

    def heartbeat_or_report_timeout(self) -> None:
        try:
            self.send_heartbeat()
        except ReferenceTimeout as reference_timeout:
            print_unavailable(reference_timeout)

    def rank_of(self, server_name: str) -> int | None:
        for available_server in self.available_servers:
            if available_server[NAME_FIELD] == server_name:
                return available_server[RANK_FIELD]
        return None

    def register(self) -> None:
        rank_response = self.reference_connector.request_rank()
        if rank_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            return

        self.rank = rank_response[PAYLOAD_FIELD][RANK_FIELD]
        print_rank(self.rank)

    def send_heartbeat(self) -> None:
        if self.rank is None:
            self.register()

        heartbeat_response = self.reference_connector.send_heartbeat()
        if self.reference_forgot_this_server(heartbeat_response):
            self.register()
            return

        if heartbeat_response[STATUS_FIELD] == ResponseStatus.SUCCESS:
            self.refresh_available_servers()

    def reference_forgot_this_server(self, heartbeat_response: dict) -> bool:
        return heartbeat_response[PAYLOAD_FIELD].get(ERROR_CODE_FIELD) == UNKNOWN_SERVER_ERROR_CODE

    def refresh_available_servers(self) -> None:
        server_list_response = self.reference_connector.request_server_list()
        if server_list_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            return

        self.available_servers = server_list_response[PAYLOAD_FIELD][SERVERS_FIELD]
        print_available_servers(self.available_servers)
