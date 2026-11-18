from connectors import ServerTopicSubscriber, decode_message
from constants import COORDINATOR_TOPIC, REPLICATION_TOPIC, SENDER_FIELD
from controllers import CoordinationController, ReplicationController
from errors import BbsError
from models import LogicalClock
from schemas import coordinator_name_from, replicated_record_message_from, valid_logical_clock_of
from utils import print_applied_record, print_ignored_topic_message, print_received_publication


class ServerTopicResource:
    def __init__(
        self,
        server_name: str,
        server_topic_subscriber: ServerTopicSubscriber,
        logical_clock: LogicalClock,
        coordination_controller: CoordinationController,
        replication_controller: ReplicationController,
    ) -> None:
        self.server_name = server_name
        self.server_topic_subscriber = server_topic_subscriber
        self.logical_clock = logical_clock
        self.coordination_controller = coordination_controller
        self.replication_controller = replication_controller
        self.handlers_by_topic = {
            COORDINATOR_TOPIC: self.handle_coordinator_announcement,
            REPLICATION_TOPIC: self.handle_replicated_record,
        }

    def receive_next_message(self) -> None:
        topic, encoded_message = self.server_topic_subscriber.receive()
        try:
            self.handle_topic_message(topic, encoded_message)
        except BbsError:
            print_ignored_topic_message(topic)

    def handle_topic_message(self, topic: str, encoded_message: bytes) -> None:
        topic_handler = self.handlers_by_topic.get(topic)
        if topic_handler is None:
            print_ignored_topic_message(topic)
            return

        decoded_message = decode_message(encoded_message)
        if self.was_sent_by_this_server(decoded_message):
            return

        print_received_publication(topic, decoded_message)
        self.observe_logical_clock_of(decoded_message)
        topic_handler(decoded_message)

    def was_sent_by_this_server(self, decoded_message: object) -> bool:
        return type(decoded_message) is dict and decoded_message.get(SENDER_FIELD) == self.server_name

    def observe_logical_clock_of(self, decoded_message: object) -> None:
        received_logical_clock = valid_logical_clock_of(decoded_message)
        if received_logical_clock is not None:
            self.logical_clock.observe(received_logical_clock)

    def handle_coordinator_announcement(self, decoded_message: object) -> None:
        self.coordination_controller.accept_coordinator_announcement(coordinator_name_from(decoded_message))

    def handle_replicated_record(self, decoded_message: object) -> None:
        record = replicated_record_message_from(decoded_message)
        if self.replication_controller.apply_remote_record(record):
            print_applied_record(record.label(), record.kind.value)
