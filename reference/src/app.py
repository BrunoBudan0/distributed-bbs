import os

from connectors import ServerConnector
from constants import DEFAULT_HEARTBEAT_TIMEOUT_MS, HEARTBEAT_TIMEOUT_VARIABLE, SERVER_FACING_ENDPOINT
from controllers import ServerRegistryController
from models import LogicalClock, ServerRegistry
from resources import RequestResource


def build_request_resource() -> RequestResource:
    heartbeat_timeout_ms = int(os.environ.get(HEARTBEAT_TIMEOUT_VARIABLE, DEFAULT_HEARTBEAT_TIMEOUT_MS))
    return RequestResource(
        server_connector=ServerConnector(SERVER_FACING_ENDPOINT),
        server_registry_controller=ServerRegistryController(ServerRegistry(heartbeat_timeout_ms)),
        logical_clock=LogicalClock(),
    )


if __name__ == "__main__":
    build_request_resource().serve_forever()
