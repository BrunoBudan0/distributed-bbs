from connectors import IncomingPoller, IncomingSource
from controllers import CoordinationController, ReferenceController
from resources.announcement_resource import AnnouncementResource
from resources.peer_resource import PeerResource
from resources.request_resource import RequestResource


class ServerLoop:
    def __init__(
        self,
        incoming_poller: IncomingPoller,
        request_resource: RequestResource,
        peer_resource: PeerResource,
        announcement_resource: AnnouncementResource,
        reference_controller: ReferenceController,
        coordination_controller: CoordinationController,
    ) -> None:
        self.incoming_poller = incoming_poller
        self.request_resource = request_resource
        self.peer_resource = peer_resource
        self.announcement_resource = announcement_resource
        self.reference_controller = reference_controller
        self.coordination_controller = coordination_controller
        self.handlers_by_source = {
            IncomingSource.CLIENT_REQUEST: self.answer_client_request,
            IncomingSource.PEER_REQUEST: self.answer_peer_request,
            IncomingSource.COORDINATOR_ANNOUNCEMENT: self.receive_coordinator_announcement,
        }

    def run_forever(self) -> None:
        self.reference_controller.register_or_report_timeout()
        self.coordination_controller.hold_election()
        while True:
            for ready_source in self.incoming_poller.ready_sources():
                self.handlers_by_source[ready_source]()

    def answer_client_request(self) -> None:
        self.request_resource.answer_next_request()
        self.reference_controller.count_client_message()
        self.coordination_controller.count_client_message()

    def answer_peer_request(self) -> None:
        self.peer_resource.answer_next_request()
        self.coordination_controller.run_pending_election()

    def receive_coordinator_announcement(self) -> None:
        self.announcement_resource.receive_next_announcement()
        self.coordination_controller.run_pending_election()
