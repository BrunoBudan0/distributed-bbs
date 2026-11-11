from collections.abc import Callable
from typing import Any

from connectors import decode_message, encode_message
from constants import ERROR_CODE_FIELD, ERROR_DESCRIPTION_FIELD, UNIDENTIFIED_OPERATION
from dtos import ResponseMessage
from errors import BbsError, MalformedMessage
from models import LogicalClock, PhysicalClock, ResponseStatus
from schemas import operation_label_of, valid_logical_clock_of
from utils import print_received_message, print_received_undecodable_bytes, print_sent_message


class MessageAnswerer:
    def __init__(
        self,
        server_name: str,
        logical_clock: LogicalClock,
        physical_clock: PhysicalClock,
        known_operation_names: tuple[str, ...],
        parse_request: Callable[[object], Any],
        handle_request: Callable[[Any], dict],
    ) -> None:
        self.server_name = server_name
        self.logical_clock = logical_clock
        self.physical_clock = physical_clock
        self.known_operation_names = known_operation_names
        self.parse_request = parse_request
        self.handle_request = handle_request

    def encoded_response_to(self, encoded_request: bytes) -> bytes:
        response_fields = self.response_to(encoded_request).as_fields()
        print_sent_message(response_fields)
        return encode_message(response_fields)

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
        operation_label = operation_label_of(decoded_message, self.known_operation_names)
        try:
            response_payload = self.handle_request(self.parse_request(decoded_message))
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
