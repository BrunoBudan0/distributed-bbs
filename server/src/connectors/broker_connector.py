import zmq


class BrokerConnector:
    def __init__(self, broker_endpoint: str) -> None:
        self.reply_socket = zmq.Context.instance().socket(zmq.REP)
        self.reply_socket.connect(broker_endpoint)

    def receive(self) -> bytes:
        return self.reply_socket.recv()

    def send(self, encoded_response: bytes) -> None:
        self.reply_socket.send(encoded_response)
