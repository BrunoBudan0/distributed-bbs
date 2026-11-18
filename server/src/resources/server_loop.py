from connectors import IncomingPoller, IncomingSource
from controllers import CoordinationController, ReferenceController, ReplicationController
from resources.peer_resource import PeerResource
from resources.request_resource import RequestResource
from resources.server_topic_resource import ServerTopicResource


class ServerLoop:
    def __init__(
        self,
        incoming_poller: IncomingPoller,
        request_resource: RequestResource,
        peer_resource: PeerResource,
        server_topic_resource: ServerTopicResource,
        reference_controller: ReferenceController,
        coordination_controller: CoordinationController,
        replication_controller: ReplicationController,
    ) -> None:
        self.incoming_poller = incoming_poller
        self.request_resource = request_resource
        self.peer_resource = peer_resource
        self.server_topic_resource = server_topic_resource
        self.reference_controller = reference_controller
        self.coordination_controller = coordination_controller
        self.replication_controller = replication_controller
        self.handlers_by_source = {
            IncomingSource.CLIENT_REQUEST: self.answer_client_request,
            IncomingSource.PEER_REQUEST: self.answer_peer_request,
            IncomingSource.SERVER_TOPIC_MESSAGE: self.receive_server_topic_message,
        }

    def run_forever(self) -> None:
        self.reference_controller.register_or_report_timeout()
        self.coordination_controller.hold_election()
        self.replication_controller.synchronize_on_new_coordinator(self.coordination_controller.coordinator_name)
        while True:
            for ready_source in self.incoming_poller.ready_sources():
                self.handlers_by_source[ready_source]()

    def answer_client_request(self) -> None:
        self.request_resource.answer_next_request()
        self.reference_controller.count_client_message()
        self.coordination_controller.count_client_message()
        self.replication_controller.count_client_message(self.coordination_controller.coordinator_name)

    def answer_peer_request(self) -> None:
        self.peer_resource.answer_next_request()
        self.coordination_controller.run_pending_election()

    def receive_server_topic_message(self) -> None:
        self.server_topic_resource.receive_next_message()
        self.coordination_controller.run_pending_election()
        self.replication_controller.synchronize_on_new_coordinator(self.coordination_controller.coordinator_name)
