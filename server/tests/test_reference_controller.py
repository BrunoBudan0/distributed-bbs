from constants import UNKNOWN_SERVER_ERROR_CODE
from controllers import ReferenceController
from fakes import available_server, error_response, success_response

CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT = 10
RANK_REQUEST = "rank"
HEARTBEAT = "heartbeat"
SERVER_LIST_REQUEST = "list_servers"
LISTED_SERVERS = [available_server("server-1", 1), available_server("server-2", 2)]


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
        return success_response({})

    def request_server_list(self) -> dict:
        self.requests.append(SERVER_LIST_REQUEST)
        return success_response({"servers": LISTED_SERVERS})


def registered_controller(reference_connector: RecordingReferenceConnector) -> ReferenceController:
    reference_controller = ReferenceController(reference_connector)
    reference_controller.register_or_report_timeout()
    reference_connector.requests.clear()
    return reference_controller


def count_client_messages(reference_controller: ReferenceController, message_count: int) -> None:
    for _ in range(message_count):
        reference_controller.count_client_message()


def test_no_heartbeat_is_sent_before_the_tenth_client_message():
    reference_connector = RecordingReferenceConnector()
    reference_controller = registered_controller(reference_connector)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT - 1)

    assert reference_connector.requests.count(HEARTBEAT) == 0


def test_one_heartbeat_is_sent_for_every_ten_client_messages():
    reference_connector = RecordingReferenceConnector()
    reference_controller = registered_controller(reference_connector)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT * 2)

    assert reference_connector.requests.count(HEARTBEAT) == 2


def test_server_without_rank_asks_for_one_before_the_heartbeat():
    reference_connector = RecordingReferenceConnector()
    reference_controller = ReferenceController(reference_connector)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert reference_connector.requests == [RANK_REQUEST, HEARTBEAT, SERVER_LIST_REQUEST]


def test_heartbeat_keeps_the_latest_list_of_available_servers_and_their_ranks():
    reference_connector = RecordingReferenceConnector()
    reference_controller = registered_controller(reference_connector)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert reference_controller.available_servers == LISTED_SERVERS
    assert reference_controller.rank_of("server-2") == 2
    assert reference_controller.rank_of("server-9") is None


def test_reference_that_forgot_the_server_triggers_a_new_rank_request():
    reference_connector = RecordingReferenceConnector(heartbeat_responses=[error_response(UNKNOWN_SERVER_ERROR_CODE)])
    reference_controller = registered_controller(reference_connector)

    count_client_messages(reference_controller, CLIENT_MESSAGES_PER_HEARTBEAT_REQUIRED_BY_THE_STATEMENT)

    assert reference_connector.requests == [HEARTBEAT, RANK_REQUEST]
