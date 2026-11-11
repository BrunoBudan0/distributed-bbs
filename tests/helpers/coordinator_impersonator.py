import msgpack
import zmq

from helpers.protocol import COORDINATOR_ANNOUNCEMENT, COORDINATOR_TOPIC
from helpers.request_exchange import current_timestamp_ms

IMPERSONATOR_LOGICAL_CLOCK = 1


class CoordinatorImpersonator:
    def __init__(self, proxy_publisher_endpoint: str) -> None:
        self.publisher_socket = zmq.Context.instance().socket(zmq.PUB)
        self.publisher_socket.setsockopt(zmq.LINGER, 0)
        self.publisher_socket.connect(proxy_publisher_endpoint)

    def announce(self, coordinator_name: str) -> None:
        announcement = {
            "operation": COORDINATOR_ANNOUNCEMENT,
            "sender": coordinator_name,
            "timestamp": current_timestamp_ms(),
            "logical_clock": IMPERSONATOR_LOGICAL_CLOCK,
            "payload": {"coordinator": coordinator_name},
        }
        self.publisher_socket.send_multipart([COORDINATOR_TOPIC.encode(), msgpack.packb(announcement)])

    def close(self) -> None:
        self.publisher_socket.close()
