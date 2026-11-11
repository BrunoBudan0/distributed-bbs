from connectors import ReferenceConnector
from constants import (
    CLIENT_MESSAGES_PER_HEARTBEAT,
    ERROR_CODE_FIELD,
    PAYLOAD_FIELD,
    RANK_FIELD,
    SERVERS_FIELD,
    STATUS_FIELD,
    TIME_FIELD,
    UNKNOWN_SERVER_ERROR_CODE,
)
from errors import ReferenceTimeout
from models import PhysicalClock, ResponseStatus
from utils import print_available_servers, print_clock_synchronization, print_rank, print_reference_timeout, system_time_ms


class ReferenceController:
    def __init__(self, reference_connector: ReferenceConnector, physical_clock: PhysicalClock) -> None:
        self.reference_connector = reference_connector
        self.physical_clock = physical_clock
        self.rank: int | None = None
        self.received_client_messages = 0

    def register_or_report_timeout(self) -> None:
        try:
            self.register()
        except ReferenceTimeout as reference_timeout:
            print_reference_timeout(reference_timeout)

    def count_client_message(self) -> None:
        self.received_client_messages += 1
        if self.received_client_messages % CLIENT_MESSAGES_PER_HEARTBEAT == 0:
            self.heartbeat_or_report_timeout()

    def heartbeat_or_report_timeout(self) -> None:
        try:
            self.send_heartbeat_and_synchronize()
        except ReferenceTimeout as reference_timeout:
            print_reference_timeout(reference_timeout)

    def register(self) -> None:
        rank_response = self.reference_connector.request_rank()
        if rank_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            return

        self.rank = rank_response[PAYLOAD_FIELD][RANK_FIELD]
        print_rank(self.rank)

    def send_heartbeat_and_synchronize(self) -> None:
        if self.rank is None:
            self.register()

        request_sent_at_ms = system_time_ms()
        heartbeat_response = self.reference_connector.send_heartbeat()
        response_received_at_ms = system_time_ms()

        if self.reference_forgot_this_server(heartbeat_response):
            self.register()
            return

        if heartbeat_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            return

        self.synchronize_physical_clock(
            heartbeat_response[PAYLOAD_FIELD][TIME_FIELD], request_sent_at_ms, response_received_at_ms
        )
        self.print_available_servers()

    def reference_forgot_this_server(self, heartbeat_response: dict) -> bool:
        return heartbeat_response[PAYLOAD_FIELD].get(ERROR_CODE_FIELD) == UNKNOWN_SERVER_ERROR_CODE

    def synchronize_physical_clock(
        self, reference_time_ms: int, request_sent_at_ms: int, response_received_at_ms: int
    ) -> None:
        offset_before_ms = self.physical_clock.offset_ms
        self.physical_clock.synchronize(reference_time_ms, request_sent_at_ms, response_received_at_ms)
        print_clock_synchronization(
            offset_before_ms, self.physical_clock.offset_ms, response_received_at_ms - request_sent_at_ms
        )

    def print_available_servers(self) -> None:
        server_list_response = self.reference_connector.request_server_list()
        print_available_servers(server_list_response[PAYLOAD_FIELD].get(SERVERS_FIELD))
