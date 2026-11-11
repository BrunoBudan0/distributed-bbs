import zmq

from constants import COORDINATOR_TOPIC


class CoordinatorSubscriber:
    def __init__(self, proxy_subscriber_endpoint: str) -> None:
        self.announcement_path_context = zmq.Context()
        self.subscriber_socket = self.announcement_path_context.socket(zmq.SUB)
        self.subscriber_socket.connect(proxy_subscriber_endpoint)
        self.subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, COORDINATOR_TOPIC)

    def receive(self) -> tuple[str, bytes]:
        encoded_topic, encoded_announcement = self.subscriber_socket.recv_multipart()
        return encoded_topic.decode(errors="replace"), encoded_announcement
