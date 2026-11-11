class ReferenceTimeout(Exception):
    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"no response from the reference within {timeout_ms} ms")


class UnexpectedReferenceResponse(Exception):
    def __init__(self, decoded_message: object) -> None:
        super().__init__(f"the reference answered outside the protocol: {decoded_message!r}")
