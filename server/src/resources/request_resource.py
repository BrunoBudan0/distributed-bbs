from connectors import BrokerConnector, decode_message, encode_message
from constants import (
    CHANNEL_FIELD,
    CHANNELS_FIELD,
    ERROR_CODE_FIELD,
    ERROR_DESCRIPTION_FIELD,
    MESSAGE_FIELD,
    UNIDENTIFIED_OPERATION,
)
from controllers import ChannelController, LoginController, PublicationController, ReferenceController
from dtos import RequestMessage, ResponseMessage
from errors import BbsError, MalformedMessage
from models import LogicalClock, Operation, PhysicalClock, Publication, ResponseStatus
from schemas import operation_label_of, request_from, valid_logical_clock_of
from utils import print_received_message, print_received_undecodable_bytes, print_sent_message


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
        reference_controller: ReferenceController,
    ) -> None:
        self.server_name = server_name
        self.broker_connector = broker_connector
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock
        self.login_controller = login_controller
        self.channel_controller = channel_controller
        self.publication_controller = publication_controller
        self.reference_controller = reference_controller
        self.operation_handlers = {
            Operation.LOGIN: self.handle_login,
            Operation.CREATE_CHANNEL: self.handle_create_channel,
            Operation.LIST_CHANNELS: self.handle_list_channels,
            Operation.PUBLISH: self.handle_publish,
        }

    def serve_forever(self) -> None:
        self.reference_controller.register_or_report_timeout()
        while True:
            self.answer_next_request()
            self.reference_controller.count_client_message()

    def answer_next_request(self) -> None:
        response = self.response_to(self.broker_connector.receive())
        response_fields = response.as_fields()
        print_sent_message(response_fields)
        self.broker_connector.send(encode_message(response_fields))

    def response_to(self, encoded_request: bytes) -> ResponseMessage:
        try:
            decoded_message = decode_message(encoded_request)
        except MalformedMessage as refusal:
            print_received_undecodable_bytes(encoded_request)
            return self.refusal_response(UNIDENTIFIED_OPERATION, refusal)

        print_received_message(decoded_message)
        return self.response_to_decoded(decoded_message)

    def response_to_decoded(self, decoded_message: object) -> ResponseMessage:
        self.observe_logical_clock_of(decoded_message)
        operation_label = operation_label_of(decoded_message)
        try:
            request = request_from(decoded_message)
            response_payload = self.operation_handlers[request.operation](request)
        except BbsError as refusal:
            return self.refusal_response(operation_label, refusal)

        return self.response(operation_label, ResponseStatus.SUCCESS, response_payload)

    def observe_logical_clock_of(self, decoded_message: object) -> None:
        received_logical_clock = valid_logical_clock_of(decoded_message)
        if received_logical_clock is not None:
            self.logical_clock.observe(received_logical_clock)

    def refusal_response(self, operation_label: str, refusal: BbsError) -> ResponseMessage:
        error_payload = {ERROR_CODE_FIELD: refusal.code, ERROR_DESCRIPTION_FIELD: refusal.description}
        return self.response(operation_label, ResponseStatus.ERROR, error_payload)

    def response(self, operation_label: str, status: ResponseStatus, payload: dict) -> ResponseMessage:
        return ResponseMessage(
            operation=operation_label,
            sender=self.server_name,
            timestamp=self.physical_clock.now_ms(),
            logical_clock=self.logical_clock.tick_for_send(),
            status=status,
            payload=payload,
        )

    def handle_login(self, request: RequestMessage) -> dict:
        self.login_controller.record_login(request.sender, request.timestamp)
        return {}

    def handle_create_channel(self, request: RequestMessage) -> dict:
        self.channel_controller.create_channel_or_refuse(
            request.payload[CHANNEL_FIELD], request.sender, request.timestamp
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
