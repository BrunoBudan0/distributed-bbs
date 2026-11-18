from connectors import BrokerConnector
from constants import CHANNEL_FIELD, CHANNELS_FIELD, MESSAGE_FIELD
from controllers import ChannelController, LoginController, PublicationController
from dtos import ChannelHistory, RequestMessage
from models import Channel, LogicalClock, Login, Operation, PhysicalClock, Publication
from resources.message_answerer import MessageAnswerer
from schemas import KNOWN_OPERATION_NAMES, request_from


class RequestResource:
    def __init__(
        self,
        server_name: str,
        broker_connector: BrokerConnector,
        logical_clock: LogicalClock,
        physical_clock: PhysicalClock,
        login_controller: LoginController,
        channel_controller: ChannelController,
        publication_controller: PublicationController,
    ) -> None:
        self.server_name = server_name
        self.broker_connector = broker_connector
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock
        self.login_controller = login_controller
        self.channel_controller = channel_controller
        self.publication_controller = publication_controller
        self.operation_handlers = {
            Operation.LOGIN: self.handle_login,
            Operation.CREATE_CHANNEL: self.handle_create_channel,
            Operation.LIST_CHANNELS: self.handle_list_channels,
            Operation.PUBLISH: self.handle_publish,
            Operation.CHANNEL_HISTORY: self.handle_channel_history,
        }
        self.message_answerer = MessageAnswerer(
            server_name, logical_clock, physical_clock, KNOWN_OPERATION_NAMES, request_from, self.handle_request
        )

    def answer_next_request(self) -> None:
        encoded_request = self.broker_connector.receive()
        self.broker_connector.send(self.message_answerer.encoded_response_to(encoded_request))

    def handle_request(self, request: RequestMessage) -> dict:
        return self.operation_handlers[request.operation](request)

    def handle_login(self, request: RequestMessage) -> dict:
        self.login_controller.record_login(Login(username=request.sender, logged_in_at_ms=request.timestamp))
        return {}

    def handle_create_channel(self, request: RequestMessage) -> dict:
        self.channel_controller.create_channel_or_refuse(
            Channel(
                name=request.payload[CHANNEL_FIELD],
                created_by_username=request.sender,
                created_at_ms=request.timestamp,
                created_logical_clock=self.logical_clock.counter,
                created_on_server=self.server_name,
            )
        )
        return {}

    def handle_list_channels(self, request: RequestMessage) -> dict:
        return {CHANNELS_FIELD: self.channel_controller.channel_names()}

    def handle_publish(self, request: RequestMessage) -> dict:
        self.publication_controller.publish_or_refuse(
            Publication(
                channel_name=request.payload[CHANNEL_FIELD],
                author_username=request.sender,
                message=request.payload[MESSAGE_FIELD],
                requested_at_ms=request.timestamp,
                published_at_ms=self.physical_clock.now_ms(),
                published_by_server=self.server_name,
            )
        )
        return {}

    def handle_channel_history(self, request: RequestMessage) -> dict:
        channel_name = request.payload[CHANNEL_FIELD]
        publications = self.publication_controller.channel_history_or_refuse(channel_name)
        return ChannelHistory(channel_name, publications).as_fields()
