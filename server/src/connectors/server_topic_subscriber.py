import zmq

from constants import SERVER_TOPICS


class ServerTopicSubscriber:
    def __init__(self, proxy_subscriber_endpoint: str) -> None:
        self.server_topic_context = zmq.Context()
        self.subscriber_socket = self.server_topic_context.socket(zmq.SUB)
        self.subscriber_socket.connect(proxy_subscriber_endpoint)
        for server_topic in SERVER_TOPICS:
            self.subscriber_socket.setsockopt_string(zmq.SUBSCRIBE, server_topic)

    def receive(self) -> tuple[str, bytes]:
        encoded_topic, encoded_message = self.subscriber_socket.recv_multipart()
        return encoded_topic.decode(errors="replace"), encoded_message
