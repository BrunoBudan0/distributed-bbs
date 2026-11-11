import zmq

from connectors.message_codec import decode_message, encode_message
from constants import (
    LOGICAL_CLOCK_FIELD,
    OPERATION_FIELD,
    PAYLOAD_FIELD,
    REFERENCE_TIMEOUT_MS,
    SENDER_FIELD,
    TIMESTAMP_FIELD,
)
from errors import ReferenceTimeout
from models import LogicalClock, PhysicalClock, ReferenceOperation
from schemas import process_response_from
from utils import print_received_message, print_sent_message


class ReferenceConnector:
    def __init__(
        self,
        reference_endpoint: str,
        server_name: str,
        logical_clock: LogicalClock,
        physical_clock: PhysicalClock,
    ) -> None:
        self.reference_endpoint = reference_endpoint
        self.server_name = server_name
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock
        self.reference_path_context = zmq.Context()
        self.request_socket = self.new_connected_socket()

    def request_rank(self) -> dict:
        return self.exchange(ReferenceOperation.RANK)

    def send_heartbeat(self) -> dict:
        return self.exchange(ReferenceOperation.HEARTBEAT)

    def request_server_list(self) -> dict:
        return self.exchange(ReferenceOperation.LIST_SERVERS)

    def exchange(self, operation: ReferenceOperation) -> dict:
        request_fields = {
            OPERATION_FIELD: operation.value,
            SENDER_FIELD: self.server_name,
            TIMESTAMP_FIELD: self.physical_clock.now_ms(),
            LOGICAL_CLOCK_FIELD: self.logical_clock.tick_for_send(),
            PAYLOAD_FIELD: {},
        }
        print_sent_message(request_fields)
        self.request_socket.send(encode_message(request_fields))

        if self.request_socket.poll(REFERENCE_TIMEOUT_MS) == 0:
            self.replace_socket()
            raise ReferenceTimeout(REFERENCE_TIMEOUT_MS)

        response_fields = process_response_from(decode_message(self.request_socket.recv()))
        print_received_message(response_fields)
        self.logical_clock.observe(response_fields[LOGICAL_CLOCK_FIELD])
        return response_fields

    def replace_socket(self) -> None:
        self.request_socket.close()
        self.request_socket = self.new_connected_socket()

    def new_connected_socket(self) -> zmq.Socket:
        request_socket = self.reference_path_context.socket(zmq.REQ)
        request_socket.setsockopt(zmq.LINGER, 0)
        request_socket.connect(self.reference_endpoint)
        return request_socket
