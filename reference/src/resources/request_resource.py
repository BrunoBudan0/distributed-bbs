from connectors import ServerConnector, decode_message, encode_message
from constants import (
    ERROR_CODE_FIELD,
    ERROR_DESCRIPTION_FIELD,
    NAME_FIELD,
    RANK_FIELD,
    REFERENCE_NAME,
    SERVERS_FIELD,
    SWEEP_INTERVAL_MS,
    TIME_FIELD,
    UNIDENTIFIED_OPERATION,
)
from controllers import ServerRegistryController
from dtos import RequestMessage, ResponseMessage
from errors import BbsError, MalformedMessage
from models import LogicalClock, Operation, ResponseStatus
from schemas import operation_label_of, request_from, valid_logical_clock_of
from utils import current_timestamp_ms, print_received_message, print_received_undecodable_bytes, print_sent_message


class RequestResource:
    def __init__(
        self,
        server_connector: ServerConnector,
        server_registry_controller: ServerRegistryController,
        logical_clock: LogicalClock,
    ) -> None:
        self.server_connector = server_connector
        self.server_registry_controller = server_registry_controller
        self.logical_clock = logical_clock
        self.operation_handlers = {
            Operation.RANK: self.handle_rank,
            Operation.LIST_SERVERS: self.handle_list_servers,
            Operation.HEARTBEAT: self.handle_heartbeat,
        }

    def serve_forever(self) -> None:
        while True:
            if self.server_connector.has_request_within(SWEEP_INTERVAL_MS):
                self.answer_next_request()
            self.server_registry_controller.remove_silent_servers()

    def answer_next_request(self) -> None:
        response = self.response_to(self.server_connector.receive())
        response_fields = response.as_fields()
        print_sent_message(response_fields)
        self.server_connector.send(encode_message(response_fields))

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
            sender=REFERENCE_NAME,
            timestamp=current_timestamp_ms(),
            logical_clock=self.logical_clock.tick_for_send(),
            status=status,
            payload=payload,
        )

    def handle_rank(self, request: RequestMessage) -> dict:
        return {RANK_FIELD: self.server_registry_controller.rank_for(request.sender)}

    def handle_list_servers(self, request: RequestMessage) -> dict:
        return {
            SERVERS_FIELD: [
                {NAME_FIELD: available_server.name, RANK_FIELD: available_server.rank}
                for available_server in self.server_registry_controller.available_servers()
            ]
        }

    def handle_heartbeat(self, request: RequestMessage) -> dict:
        self.server_registry_controller.record_heartbeat(request.sender)
        return {TIME_FIELD: current_timestamp_ms()}
