class ReferenceTimeout(Exception):
    def __init__(self, timeout_ms: int) -> None:
        super().__init__(f"no response from the reference within {timeout_ms} ms")


class PeerUnavailable(Exception):
    def __init__(self, peer_name: str) -> None:
        super().__init__(f"the server {peer_name!r} did not answer")


class OutdatedDatabase(Exception):
    def __init__(self, stored_schema_version: int, expected_schema_version: int) -> None:
        super().__init__(
            f"the data volume uses schema version {stored_schema_version} and this server needs version "
            f"{expected_schema_version}; run docker compose down -v to start with fresh volumes"
        )


class UnexpectedProcessResponse(Exception):
    def __init__(self, decoded_message: object) -> None:
        super().__init__(f"another process answered outside the protocol: {decoded_message!r}")
