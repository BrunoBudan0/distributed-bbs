import time

import msgpack
import zmq

from helpers.protocol import MAX_LOGICAL_CLOCK

RESPONSE_TIMEOUT_MS = 15000
MILLISECONDS_PER_SECOND = 1000


def current_timestamp_ms() -> int:
    return int(time.time() * MILLISECONDS_PER_SECOND)


class LogicalCounter:
    def __init__(self) -> None:
        self.value = 0

    def tick(self) -> int:
        self.value = min(self.value + 1, MAX_LOGICAL_CLOCK)
        return self.value

    def observe(self, received_value: object) -> None:
        if type(received_value) is int:
            self.value = max(self.value, received_value)


def exchange_over_request_socket(endpoint: str, encoded_request: bytes) -> dict:
    request_socket = zmq.Context.instance().socket(zmq.REQ)
    request_socket.setsockopt(zmq.RCVTIMEO, RESPONSE_TIMEOUT_MS)
    request_socket.setsockopt(zmq.LINGER, 0)
    request_socket.connect(endpoint)
    try:
        request_socket.send(encoded_request)
        return msgpack.unpackb(request_socket.recv())
    finally:
        request_socket.close()


class RequestClient:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.logical_counter = LogicalCounter()

    def exchange_bytes(self, encoded_request: bytes) -> dict:
        response = exchange_over_request_socket(self.endpoint, encoded_request)
        self.logical_counter.observe(response.get("logical_clock"))
        return response

    def exchange_message(self, message: object) -> dict:
        return self.exchange_bytes(msgpack.packb(message))

    def valid_request(
        self,
        operation: str,
        sender: str,
        payload: dict,
        timestamp: int | None = None,
        logical_clock: int | None = None,
    ) -> dict:
        return {
            "operation": operation,
            "sender": sender,
            "timestamp": current_timestamp_ms() if timestamp is None else timestamp,
            "logical_clock": self.logical_counter.tick() if logical_clock is None else logical_clock,
            "payload": payload,
        }
