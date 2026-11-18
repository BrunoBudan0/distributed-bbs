from connectors import PeerServerConnector
from constants import RECORDS_FIELD, TIME_FIELD, WATERMARKS_FIELD
from controllers import CoordinationController, ReplicationController
from dtos import PeerRequestMessage
from models import LogicalClock, PeerOperation, PhysicalClock
from resources.message_answerer import MessageAnswerer
from schemas import KNOWN_PEER_OPERATION_NAMES, peer_request_from, replicated_records_from, watermarks_from


class PeerResource:
    def __init__(
        self,
        server_name: str,
        peer_server_connector: PeerServerConnector,
        logical_clock: LogicalClock,
        physical_clock: PhysicalClock,
        coordination_controller: CoordinationController,
        replication_controller: ReplicationController,
    ) -> None:
        self.peer_server_connector = peer_server_connector
        self.coordination_controller = coordination_controller
        self.replication_controller = replication_controller
        self.operation_handlers = {
            PeerOperation.ELECTION: self.handle_election,
            PeerOperation.CLOCK: self.handle_clock,
            PeerOperation.REPLICATION_SYNC: self.handle_replication_sync,
            PeerOperation.REPLICATION_PUSH: self.handle_replication_push,
        }
        self.message_answerer = MessageAnswerer(
            server_name,
            logical_clock,
            physical_clock,
            KNOWN_PEER_OPERATION_NAMES,
            peer_request_from,
            self.handle_request,
        )

    def answer_next_request(self) -> None:
        encoded_request = self.peer_server_connector.receive()
        self.peer_server_connector.send(self.message_answerer.encoded_response_to(encoded_request))

    def handle_request(self, request: PeerRequestMessage) -> dict:
        return self.operation_handlers[request.operation](request)

    def handle_election(self, request: PeerRequestMessage) -> dict:
        self.coordination_controller.answer_election()
        return {}

    def handle_clock(self, request: PeerRequestMessage) -> dict:
        return {TIME_FIELD: self.coordination_controller.answer_clock_request(request.sender, request.timestamp)}

    def handle_replication_sync(self, request: PeerRequestMessage) -> dict:
        missing_records, own_watermarks = self.replication_controller.answer_synchronization(
            watermarks_from(request.payload)
        )
        return {
            RECORDS_FIELD: [record.as_fields() for record in missing_records],
            WATERMARKS_FIELD: own_watermarks,
        }

    def handle_replication_push(self, request: PeerRequestMessage) -> dict:
        self.replication_controller.accept_pushed_records(replicated_records_from(request.payload))
        return {}
