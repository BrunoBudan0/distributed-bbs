import zmq


class BrokerConnector:
    def __init__(self, broker_endpoint: str) -> None:
        self.request_path_context = zmq.Context()
        self.reply_socket = self.request_path_context.socket(zmq.REP)
        self.reply_socket.connect(broker_endpoint)

    def receive(self) -> bytes:
        return self.reply_socket.recv()

    def send(self, encoded_response: bytes) -> None:
        self.reply_socket.send(encoded_response)
