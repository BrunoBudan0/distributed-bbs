import pytest

from controllers import CoordinationController
from errors import NotCoordinator
from fakes import (
    CLOCK,
    ELECTION,
    FakeReferenceController,
    RecordingChannelPublisher,
    RecordingPeerConnector,
    available_server,
    error_response,
    success_response,
)
from models import BerkeleyCoordinator, PhysicalClock
from utils import system_time_ms

CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT = 15
OWN_NAME = "server-2"
OWN_RANK = 2
LOWER_SERVER = available_server("server-1", 1)
OWN_SERVER = available_server(OWN_NAME, OWN_RANK)
HIGHER_SERVER = available_server("server-3", 3)
HIGHEST_SERVER = available_server("server-4", 4)
READING_VALIDITY_MS = 60_000
COORDINATOR_AHEAD_BY_MS = 5_000
REQUESTER_AHEAD_BY_MS = 7_000
SYNCHRONIZATION_TOLERANCE_MS = 50


class CoordinationScenario:
    def __init__(
        self,
        available_servers: list[dict],
        own_rank: int | None = OWN_RANK,
        peer_connector: RecordingPeerConnector | None = None,
    ) -> None:
        self.peer_connector = peer_connector or RecordingPeerConnector()
        self.channel_publisher = RecordingChannelPublisher()
        self.physical_clock = PhysicalClock(0, system_time_ms)
        self.controller = CoordinationController(
            OWN_NAME,
            FakeReferenceController(own_rank, available_servers),
            self.peer_connector,
            self.channel_publisher,
            self.physical_clock,
            BerkeleyCoordinator(READING_VALIDITY_MS),
        )

    def count_client_messages(self, message_count: int) -> None:
        for _ in range(message_count):
            self.controller.count_client_message()


def test_server_with_no_higher_ranked_peer_becomes_coordinator_and_announces_itself():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER])

    scenario.controller.hold_election()

    assert scenario.peer_connector.requests == []
    assert scenario.controller.coordinator_name == OWN_NAME
    assert scenario.channel_publisher.announced_coordinators == [OWN_NAME]


def test_election_is_asked_only_of_higher_ranked_servers_and_waits_when_one_answers():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER, HIGHER_SERVER, HIGHEST_SERVER])

    scenario.controller.hold_election()

    assert scenario.peer_connector.requests == [("server-3", ELECTION), ("server-4", ELECTION)]
    assert scenario.controller.coordinator_name is None
    assert scenario.channel_publisher.announced_coordinators == []


def test_server_becomes_coordinator_when_no_higher_ranked_server_answers():
    scenario = CoordinationScenario(
        [OWN_SERVER, HIGHER_SERVER], peer_connector=RecordingPeerConnector(unavailable_peer_names=("server-3",))
    )

    scenario.controller.hold_election()

    assert scenario.controller.coordinator_name == OWN_NAME
    assert scenario.channel_publisher.announced_coordinators == [OWN_NAME]


def test_server_without_rank_does_not_hold_an_election():
    scenario = CoordinationScenario([OWN_SERVER, HIGHER_SERVER], own_rank=None)

    scenario.controller.hold_election()

    assert scenario.peer_connector.requests == []
    assert scenario.controller.coordinator_name is None


def test_clock_is_synchronized_with_the_coordinator_on_every_fifteenth_client_message():
    scenario = CoordinationScenario([OWN_SERVER, HIGHER_SERVER])
    scenario.controller.accept_coordinator_announcement("server-3")

    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT - 1)
    clock_requests_before_the_fifteenth = list(scenario.peer_connector.requests)
    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT + 1)

    assert clock_requests_before_the_fifteenth == []
    assert scenario.peer_connector.requests == [("server-3", CLOCK), ("server-3", CLOCK)]


def test_coordinator_does_not_ask_anyone_for_the_clock():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER])
    scenario.controller.hold_election()

    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT)

    assert scenario.peer_connector.requests == []


def test_coordinator_time_moves_the_physical_clock_with_half_of_the_round_trip():
    coordinator_time_response = success_response({"time": system_time_ms() + COORDINATOR_AHEAD_BY_MS})
    scenario = CoordinationScenario(
        [OWN_SERVER, HIGHER_SERVER], peer_connector=RecordingPeerConnector(clock_response=coordinator_time_response)
    )
    scenario.controller.accept_coordinator_announcement("server-3")

    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT)

    assert abs(scenario.physical_clock.offset_ms - COORDINATOR_AHEAD_BY_MS) <= SYNCHRONIZATION_TOLERANCE_MS


def test_unreachable_coordinator_leads_to_an_election():
    scenario = CoordinationScenario(
        [OWN_SERVER, HIGHER_SERVER], peer_connector=RecordingPeerConnector(unavailable_peer_names=("server-3",))
    )
    scenario.controller.accept_coordinator_announcement("server-3")

    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT)

    assert scenario.peer_connector.requests == [("server-3", CLOCK), ("server-3", ELECTION)]
    assert scenario.controller.coordinator_name == OWN_NAME


def test_refusal_from_a_server_that_stopped_being_coordinator_leads_to_an_election():
    scenario = CoordinationScenario(
        [OWN_SERVER, HIGHER_SERVER],
        peer_connector=RecordingPeerConnector(clock_response=error_response("NOT_COORDINATOR")),
    )
    scenario.controller.accept_coordinator_announcement("server-3")

    scenario.count_client_messages(CLIENT_MESSAGES_PER_CLOCK_SYNCHRONIZATION_REQUIRED_BY_THE_STATEMENT)

    assert scenario.peer_connector.requests == [("server-3", CLOCK), ("server-3", ELECTION)]


def test_announcement_from_a_lower_ranked_server_leads_to_an_election_that_this_server_wins():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER])

    scenario.controller.accept_coordinator_announcement("server-1")
    scenario.controller.run_pending_election()

    assert scenario.controller.coordinator_name == OWN_NAME
    assert scenario.channel_publisher.announced_coordinators == [OWN_NAME]


def test_announcement_from_a_higher_ranked_server_is_accepted_without_an_election():
    scenario = CoordinationScenario([OWN_SERVER, HIGHER_SERVER])

    scenario.controller.accept_coordinator_announcement("server-3")
    scenario.controller.run_pending_election()

    assert scenario.controller.coordinator_name == "server-3"
    assert scenario.peer_connector.requests == []


def test_election_request_from_a_peer_leads_to_an_own_election_after_answering():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER])

    scenario.controller.answer_election()
    coordinator_right_after_answering = scenario.controller.coordinator_name
    scenario.controller.run_pending_election()

    assert coordinator_right_after_answering is None
    assert scenario.controller.coordinator_name == OWN_NAME


def test_clock_request_to_a_server_that_is_not_coordinator_is_refused():
    scenario = CoordinationScenario([OWN_SERVER, HIGHER_SERVER])
    scenario.controller.accept_coordinator_announcement("server-3")

    with pytest.raises(NotCoordinator):
        scenario.controller.answer_clock_request("server-1", system_time_ms())


def test_coordinator_answers_with_the_berkeley_average_and_moves_its_own_clock():
    scenario = CoordinationScenario([LOWER_SERVER, OWN_SERVER])
    scenario.controller.hold_election()
    time_before_answering_ms = system_time_ms()

    answered_time_ms = scenario.controller.answer_clock_request(
        "server-1", time_before_answering_ms + REQUESTER_AHEAD_BY_MS
    )

    expected_adjustment_ms = REQUESTER_AHEAD_BY_MS // 2
    assert abs(scenario.physical_clock.offset_ms - expected_adjustment_ms) <= SYNCHRONIZATION_TOLERANCE_MS
    assert abs(answered_time_ms - (time_before_answering_ms + expected_adjustment_ms)) <= SYNCHRONIZATION_TOLERANCE_MS
