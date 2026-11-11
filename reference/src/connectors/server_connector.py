import zmq


class ServerConnector:
    def __init__(self, server_facing_endpoint: str) -> None:
        self.server_path_context = zmq.Context()
        self.reply_socket = self.server_path_context.socket(zmq.REP)
        self.reply_socket.bind(server_facing_endpoint)

    def has_request_within(self, timeout_ms: int) -> bool:
        return self.reply_socket.poll(timeout_ms) != 0

    def receive(self) -> bytes:
        return self.reply_socket.recv()

    def send(self, encoded_response: bytes) -> None:
        self.reply_socket.send(encoded_response)
