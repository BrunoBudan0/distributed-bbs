from connectors import ChannelPublisher, PeerConnector
from constants import (
    CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION,
    NAME_FIELD,
    PAYLOAD_FIELD,
    RANK_FIELD,
    STATUS_FIELD,
    TIME_FIELD,
)
from controllers.reference_controller import ReferenceController
from errors import NotCoordinator, PeerUnavailable
from models import BerkeleyCoordinator, PhysicalClock, ResponseStatus
from utils import (
    monotonic_ms,
    print_announced_coordinator,
    print_became_coordinator,
    print_berkeley_round,
    print_clock_synchronization,
    print_election_postponed,
    print_election_started,
    print_unavailable,
    print_waiting_for_coordinator,
    system_time_ms,
)


class CoordinationController:
    def __init__(
        self,
        server_name: str,
        reference_controller: ReferenceController,
        peer_connector: PeerConnector,
        channel_publisher: ChannelPublisher,
        physical_clock: PhysicalClock,
        berkeley_coordinator: BerkeleyCoordinator,
    ) -> None:
        self.server_name = server_name
        self.reference_controller = reference_controller
        self.peer_connector = peer_connector
        self.channel_publisher = channel_publisher
        self.physical_clock = physical_clock
        self.berkeley_coordinator = berkeley_coordinator
        self.coordinator_name: str | None = None
        self.election_is_pending = False
        self.received_client_messages = 0

    def count_client_message(self) -> None:
        self.received_client_messages += 1
        if self.received_client_messages % CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION == 0:
            self.synchronize_clock_with_coordinator()

    def synchronize_clock_with_coordinator(self) -> None:
        if self.coordinator_name is None:
            self.hold_election()
            return

        if self.coordinator_name == self.server_name:
            return

        try:
            self.adopt_coordinator_time()
        except PeerUnavailable as unavailable_coordinator:
            print_unavailable(unavailable_coordinator)
            self.hold_election()

    def adopt_coordinator_time(self) -> None:
        coordinator_name = self.coordinator_name
        request_sent_at_ms = system_time_ms()
        clock_response = self.peer_connector.request_clock(coordinator_name)
        response_received_at_ms = system_time_ms()

        if clock_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            self.hold_election()
            return

        offset_before_ms = self.physical_clock.offset_ms
        self.physical_clock.synchronize(
            clock_response[PAYLOAD_FIELD][TIME_FIELD], request_sent_at_ms, response_received_at_ms
        )
        print_clock_synchronization(
            coordinator_name,
            offset_before_ms,
            self.physical_clock.offset_ms,
            response_received_at_ms - request_sent_at_ms,
        )

    def hold_election(self) -> None:
        self.election_is_pending = False
        own_rank = self.reference_controller.rank
        if own_rank is None:
            print_election_postponed()
            return

        self.reference_controller.refresh_available_servers_or_report_timeout()
        higher_ranked_server_names = self.higher_ranked_server_names(own_rank)
        print_election_started(higher_ranked_server_names)

        if self.any_server_answered_election(higher_ranked_server_names):
            self.coordinator_name = None
            print_waiting_for_coordinator()
            return

        self.become_coordinator()

    def higher_ranked_server_names(self, own_rank: int) -> list[str]:
        return [
            available_server[NAME_FIELD]
            for available_server in self.reference_controller.available_servers
            if available_server[RANK_FIELD] > own_rank
        ]

    def any_server_answered_election(self, server_names: list[str]) -> bool:
        election_answers = [self.server_answered_election(server_name) for server_name in server_names]
        return any(election_answers)

    def server_answered_election(self, server_name: str) -> bool:
        try:
            election_response = self.peer_connector.request_election(server_name)
        except PeerUnavailable as unavailable_server:
            print_unavailable(unavailable_server)
            return False

        return election_response[STATUS_FIELD] == ResponseStatus.SUCCESS

    def become_coordinator(self) -> None:
        self.coordinator_name = self.server_name
        print_became_coordinator()
        self.channel_publisher.announce_coordinator(self.server_name, self.physical_clock.now_ms())

    def answer_election(self) -> None:
        self.election_is_pending = True

    def answer_clock_request(self, requester_name: str, requester_time_ms: int) -> int:
        if self.coordinator_name != self.server_name:
            raise NotCoordinator()

        requester_offset_ms = requester_time_ms - self.physical_clock.now_ms()
        adjustment_ms = self.berkeley_coordinator.adjustment_after_reading(
            requester_name, requester_offset_ms, monotonic_ms()
        )
        self.physical_clock.shift(adjustment_ms)
        print_berkeley_round(requester_name, requester_offset_ms, adjustment_ms, self.physical_clock.offset_ms)
        return self.physical_clock.now_ms()

    def run_pending_election(self) -> None:
        if self.election_is_pending:
            self.hold_election()

    def accept_coordinator_announcement(self, coordinator_name: str) -> None:
        self.coordinator_name = coordinator_name
        print_announced_coordinator(coordinator_name)
        if self.ranks_below_this_server(coordinator_name):
            self.election_is_pending = True

    def ranks_below_this_server(self, server_name: str) -> bool:
        own_rank = self.reference_controller.rank
        announced_rank = self.reference_controller.rank_of(server_name)
        return own_rank is not None and announced_rank is not None and announced_rank < own_rank
