from enum import StrEnum

import zmq

from connectors.broker_connector import BrokerConnector
from connectors.peer_server_connector import PeerServerConnector
from connectors.server_topic_subscriber import ServerTopicSubscriber


class IncomingSource(StrEnum):
    CLIENT_REQUEST = "client_request"
    PEER_REQUEST = "peer_request"
    SERVER_TOPIC_MESSAGE = "server_topic_message"


class IncomingPoller:
    def __init__(
        self,
        broker_connector: BrokerConnector,
        peer_server_connector: PeerServerConnector,
        server_topic_subscriber: ServerTopicSubscriber,
    ) -> None:
        self.source_by_socket = {
            broker_connector.reply_socket: IncomingSource.CLIENT_REQUEST,
            peer_server_connector.reply_socket: IncomingSource.PEER_REQUEST,
            server_topic_subscriber.subscriber_socket: IncomingSource.SERVER_TOPIC_MESSAGE,
        }
        self.poller = zmq.Poller()
        for listening_socket in self.source_by_socket:
            self.poller.register(listening_socket, zmq.POLLIN)

    def ready_sources(self) -> list[IncomingSource]:
        return [self.source_by_socket[ready_socket] for ready_socket, _ in self.poller.poll()]
