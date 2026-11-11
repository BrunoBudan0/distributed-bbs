import zmq

from constants import PEER_FACING_ENDPOINT


class PeerServerConnector:
    def __init__(self) -> None:
        self.peer_facing_context = zmq.Context()
        self.reply_socket = self.peer_facing_context.socket(zmq.REP)
        self.reply_socket.bind(PEER_FACING_ENDPOINT)

    def receive(self) -> bytes:
        return self.reply_socket.recv()

    def send(self, encoded_response: bytes) -> None:
        self.reply_socket.send(encoded_response)
