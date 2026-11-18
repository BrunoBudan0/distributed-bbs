import zmq

from connectors.message_codec import encode_message
from constants import COORDINATOR_TOPIC, REPLICATION_TOPIC
from dtos import CoordinatorAnnouncement, PublicationMessage, ReplicationMessage
from models import LogicalClock, Publication, ReplicatedRecord
from utils import print_sent_publication


class ChannelPublisher:
    def __init__(self, proxy_endpoint: str, logical_clock: LogicalClock) -> None:
        self.logical_clock = logical_clock
        self.publication_path_context = zmq.Context()
        self.publisher_socket = self.publication_path_context.socket(zmq.PUB)
        self.publisher_socket.connect(proxy_endpoint)

    def publish(self, publication: Publication) -> None:
        publication_message = PublicationMessage.from_publication(publication, self.logical_clock.tick_for_send())
        self.send_on_topic(publication.channel_name, publication_message.as_fields())

    def announce_coordinator(self, coordinator_name: str, sent_at_ms: int) -> None:
        announcement = CoordinatorAnnouncement.of_coordinator(
            coordinator_name, sent_at_ms, self.logical_clock.tick_for_send()
        )
        self.send_on_topic(COORDINATOR_TOPIC, announcement.as_fields())

    def share_record(self, record: ReplicatedRecord, sender_name: str, sent_at_ms: int) -> None:
        replication_message = ReplicationMessage.of_record(
            record, sender_name, sent_at_ms, self.logical_clock.tick_for_send()
        )
        self.send_on_topic(REPLICATION_TOPIC, replication_message.as_fields())

    def send_on_topic(self, topic: str, message_fields: dict) -> None:
        print_sent_publication(topic, message_fields)
        self.publisher_socket.send_multipart([topic.encode(), encode_message(message_fields)])
