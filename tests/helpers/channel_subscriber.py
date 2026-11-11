from dataclasses import dataclass

import msgpack
import zmq

from helpers.request_exchange import current_timestamp_ms

PUBLICATION_TIMEOUT_MS = 10000


@dataclass(frozen=True)
class ReceivedPublication:
    topic: str
    fields: dict
    received_at_ms: int

    def message(self) -> str:
        return self.fields["payload"]["message"]


class ChannelSubscriber:
    def __init__(self, proxy_endpoint: str) -> None:
        self.subscriber_socket = zmq.Context.instance().socket(zmq.SUB)
        self.subscriber_socket.setsockopt(zmq.LINGER, 0)
        self.subscriber_socket.connect(proxy_endpoint)

    def subscribe(self, channel_name: str) -> None:
        self.subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, channel_name)

    def next_publication_within(self, timeout_ms: int) -> ReceivedPublication | None:
        if self.subscriber_socket.poll(timeout_ms) == 0:
            return None

        encoded_topic, encoded_publication = self.subscriber_socket.recv_multipart()
        return ReceivedPublication(
            topic=encoded_topic.decode(),
            fields=msgpack.unpackb(encoded_publication),
            received_at_ms=current_timestamp_ms(),
        )

    def next_publication(self) -> ReceivedPublication:
        publication = self.next_publication_within(PUBLICATION_TIMEOUT_MS)
        assert publication is not None, f"no publication arrived within {PUBLICATION_TIMEOUT_MS} ms"
        return publication

    def close(self) -> None:
        self.subscriber_socket.close()
