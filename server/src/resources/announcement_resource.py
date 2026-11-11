from connectors import CoordinatorSubscriber, decode_message
from constants import COORDINATOR_TOPIC
from controllers import CoordinationController
from errors import MalformedMessage
from models import LogicalClock
from schemas import coordinator_name_from, valid_logical_clock_of
from utils import print_ignored_announcement, print_received_publication


class AnnouncementResource:
    def __init__(
        self,
        coordinator_subscriber: CoordinatorSubscriber,
        logical_clock: LogicalClock,
        coordination_controller: CoordinationController,
    ) -> None:
        self.coordinator_subscriber = coordinator_subscriber
        self.logical_clock = logical_clock
        self.coordination_controller = coordination_controller

    def receive_next_announcement(self) -> None:
        topic, encoded_announcement = self.coordinator_subscriber.receive()
        try:
            coordinator_name = self.announced_coordinator_name(topic, encoded_announcement)
        except MalformedMessage:
            print_ignored_announcement(f"message on topic {topic!r} is not a coordinator announcement")
            return

        self.coordination_controller.accept_coordinator_announcement(coordinator_name)

    def announced_coordinator_name(self, topic: str, encoded_announcement: bytes) -> str:
        if topic != COORDINATOR_TOPIC:
            raise MalformedMessage()

        decoded_announcement = decode_message(encoded_announcement)
        print_received_publication(topic, decoded_announcement)
        self.observe_logical_clock_of(decoded_announcement)
        return coordinator_name_from(decoded_announcement)

    def observe_logical_clock_of(self, decoded_announcement: object) -> None:
        received_logical_clock = valid_logical_clock_of(decoded_announcement)
        if received_logical_clock is not None:
            self.logical_clock.observe(received_logical_clock)
