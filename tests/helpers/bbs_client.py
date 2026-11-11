import time

import msgpack
import zmq

from helpers.names import new_username
from helpers.protocol import CREATE_CHANNEL, LIST_CHANNELS, LOGIN, PUBLISH

RESPONSE_TIMEOUT_MS = 15000
MILLISECONDS_PER_SECOND = 1000


def current_timestamp_ms() -> int:
    return int(time.time() * MILLISECONDS_PER_SECOND)


class BbsClient:
    def __init__(self, broker_endpoint: str) -> None:
        self.broker_endpoint = broker_endpoint

    def exchange_bytes(self, encoded_request: bytes) -> dict:
        request_socket = zmq.Context.instance().socket(zmq.REQ)
        request_socket.setsockopt(zmq.RCVTIMEO, RESPONSE_TIMEOUT_MS)
        request_socket.setsockopt(zmq.LINGER, 0)
        request_socket.connect(self.broker_endpoint)
        try:
            request_socket.send(encoded_request)
            return msgpack.unpackb(request_socket.recv())
        finally:
            request_socket.close()

    def exchange_message(self, message: object) -> dict:
        return self.exchange_bytes(msgpack.packb(message))

    def valid_request(self, operation: str, sender: str, payload: dict, timestamp: int) -> dict:
        return {"operation": operation, "sender": sender, "timestamp": timestamp, "payload": payload}

    def log_in(self, username: str, timestamp: int | None = None) -> dict:
        login_timestamp = current_timestamp_ms() if timestamp is None else timestamp
        return self.exchange_message(self.valid_request(LOGIN, username, {}, login_timestamp))

    def create_channel(self, channel_name: object, creator_username: str | None = None) -> dict:
        sender = new_username() if creator_username is None else creator_username
        return self.exchange_message(
            self.valid_request(CREATE_CHANNEL, sender, {"channel": channel_name}, current_timestamp_ms())
        )

    def list_channels(self) -> dict:
        return self.exchange_message(self.valid_request(LIST_CHANNELS, new_username(), {}, current_timestamp_ms()))

    def listed_channel_names(self) -> list[str]:
        return self.list_channels()["payload"]["channels"]

    def publish(
        self,
        channel_name: object,
        message: object,
        author_username: str | None = None,
        timestamp: int | None = None,
    ) -> dict:
        sender = new_username() if author_username is None else author_username
        request_timestamp = current_timestamp_ms() if timestamp is None else timestamp
        return self.exchange_message(
            self.valid_request(PUBLISH, sender, {"channel": channel_name, "message": message}, request_timestamp)
        )
