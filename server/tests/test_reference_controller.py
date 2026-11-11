from constants import UNKNOWN_SERVER_ERROR_CODE
from controllers import ReferenceController
from models import PhysicalClock
from utils import system_time_ms

CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT = 10
SIMULATED_SKEW_MS = 7_000
SYNCHRONIZATION_TOLERANCE_MS = 50
RANK_REQUEST = "rank"
HEARTBEAT = "heartbeat"
SERVER_LIST_REQUEST = "list_servers"


def success_response(payload: dict) -> dict:
    return {"status": "success", "logical_clock": 1, "payload": payload}


def unknown_server_response() -> dict:
    return {"status": "error", "logical_clock": 1, "payload": {"error_code": UNKNOWN_SERVER_ERROR_CODE}}


class RecordingReferenceConnector:
    def __init__(self, heartbeat_responses: list[dict] | None = None) -> None:
        self.requests: list[str] = []
        self.heartbeat_responses = heartbeat_responses or []

    def request_rank(self) -> dict:
        self.requests.append(RANK_REQUEST)
        return success_response({"rank": 1})

    def send_heartbeat(self) -> dict:
        self.requests.append(HEARTBEAT)
        if self.heartbeat_responses:
            return self.heartbeat_responses.pop(0)
        return success_response({"time": system_time_ms()})

    def request_server_list(self) -> dict:
        self.requests.append(SERVER_LIST_REQUEST)
        return success_response({"servers": []})


def registered_controller(reference_connector: RecordingReferenceConnector, physical_clock: PhysicalClock):
    reference_controller = ReferenceController(reference_connector, physical_clock)
    reference_controller.register_or_report_timeout()
    reference_connector.requests.clear()
    return reference_controller


def count_client_messages(reference_controller: ReferenceController, message_count: int) -> None:
    for _ in range(message_count):
        reference_controller.count_client_message()


def test_no_heartbeat_is_sent_before_the_tenth_client_message():
    reference_connector = RecordingReferenceConnector()
    reference_controller = registered_controller(reference_connector, PhysicalClock(0, system_time_ms))

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT - 1)

    assert reference_connector.requests.count(HEARTBEAT) == 0


def test_one_heartbeat_is_sent_for_every_ten_client_messages():
    reference_connector = RecordingReferenceConnector()
    reference_controller = registered_controller(reference_connector, PhysicalClock(0, system_time_ms))

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT * 2)

    assert reference_connector.requests.count(HEARTBEAT) == 2


def test_server_without_rank_asks_for_one_before_the_heartbeat():
    reference_connector = RecordingReferenceConnector()
    reference_controller = ReferenceController(reference_connector, PhysicalClock(0, system_time_ms))

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert reference_connector.requests == [RANK_REQUEST, HEARTBEAT, SERVER_LIST_REQUEST]


def test_successful_heartbeat_brings_a_skewed_physical_clock_to_the_reference_time():
    reference_connector = RecordingReferenceConnector()
    physical_clock = PhysicalClock(SIMULATED_SKEW_MS, system_time_ms)
    reference_controller = registered_controller(reference_connector, physical_clock)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert abs(physical_clock.offset_ms) <= SYNCHRONIZATION_TOLERANCE_MS


def test_reference_that_forgot_the_server_triggers_a_new_rank_request_without_touching_the_clock():
    reference_connector = RecordingReferenceConnector(heartbeat_responses=[unknown_server_response()])
    physical_clock = PhysicalClock(SIMULATED_SKEW_MS, system_time_ms)
    reference_controller = registered_controller(reference_connector, physical_clock)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert reference_connector.requests == [HEARTBEAT, RANK_REQUEST]
    assert physical_clock.offset_ms == SIMULATED_SKEW_MS
