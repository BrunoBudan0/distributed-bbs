import zmq

from connectors.message_codec import encode_message
from dtos import PublicationMessage
from models import LogicalClock, Publication
from utils import print_sent_publication


class ChannelPublisher:
    def __init__(self, proxy_endpoint: str, logical_clock: LogicalClock) -> None:
        self.logical_clock = logical_clock
        self.publication_path_context = zmq.Context()
        self.publisher_socket = self.publication_path_context.socket(zmq.PUB)
        self.publisher_socket.connect(proxy_endpoint)

    def publish(self, publication: Publication) -> None:
        publication_message = PublicationMessage.from_publication(publication, self.logical_clock.tick_for_send())
        publication_fields = publication_message.as_fields()
        print_sent_publication(publication.channel_name, publication_fields)
        self.publisher_socket.send_multipart(
            [publication.channel_name.encode(), encode_message(publication_fields)]
        )
