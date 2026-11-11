import zmq

from connectors.message_codec import decode_message, encode_message
from constants import (
    LOGICAL_CLOCK_FIELD,
    OPERATION_FIELD,
    PAYLOAD_FIELD,
    PEER_PORT,
    PEER_TIMEOUT_MS,
    SENDER_FIELD,
    TIMESTAMP_FIELD,
)
from errors import PeerUnavailable
from models import LogicalClock, PeerOperation, PhysicalClock
from schemas import process_response_from
from utils import print_received_message, print_sent_message


def peer_endpoint(peer_name: str) -> str:
    return f"tcp://{peer_name}:{PEER_PORT}"


class PeerConnector:
    def __init__(self, server_name: str, logical_clock: LogicalClock, physical_clock: PhysicalClock) -> None:
        self.server_name = server_name
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock
        self.peer_path_context = zmq.Context()

    def request_election(self, peer_name: str) -> dict:
        return self.exchange(peer_name, PeerOperation.ELECTION)

    def request_clock(self, peer_name: str) -> dict:
        return self.exchange(peer_name, PeerOperation.CLOCK)

    def exchange(self, peer_name: str, operation: PeerOperation) -> dict:
        request_fields = {
            OPERATION_FIELD: operation.value,
            SENDER_FIELD: self.server_name,
            TIMESTAMP_FIELD: self.physical_clock.now_ms(),
            LOGICAL_CLOCK_FIELD: self.logical_clock.tick_for_send(),
            PAYLOAD_FIELD: {},
        }
        print_sent_message(request_fields)
        encoded_response = self.encoded_response_or_unavailable(peer_name, encode_message(request_fields))

        response_fields = process_response_from(decode_message(encoded_response))
        print_received_message(response_fields)
        self.logical_clock.observe(response_fields[LOGICAL_CLOCK_FIELD])
        return response_fields

    def encoded_response_or_unavailable(self, peer_name: str, encoded_request: bytes) -> bytes:
        request_socket = self.peer_path_context.socket(zmq.REQ)
        request_socket.setsockopt(zmq.LINGER, 0)
        try:
            request_socket.connect(peer_endpoint(peer_name))
            request_socket.send(encoded_request)
            if request_socket.poll(PEER_TIMEOUT_MS) == 0:
                raise PeerUnavailable(peer_name)
            return request_socket.recv()
        except zmq.ZMQError as connection_error:
            raise PeerUnavailable(peer_name) from connection_error
        finally:
            request_socket.close()
