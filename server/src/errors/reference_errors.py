class ReferenceTimeout(Exception):
    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"no response from the reference within {timeout_ms} ms")


class PeerUnavailable(Exception):
    def __init__(self, peer_name: str) -> None:
        super().__init__(f"the server {peer_name!r} did not answer")


class UnexpectedProcessResponse(Exception):
    def __init__(self, decoded_message: object) -> None:
        super().__init__(f"another process answered outside the protocol: {decoded_message!r}")
