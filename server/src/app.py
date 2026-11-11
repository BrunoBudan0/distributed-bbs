import os

from connectors import BrokerConnector, ChannelPublisher, ReferenceConnector
from constants import DATABASE_PATH, DEFAULT_SIMULATED_CLOCK_SKEW_MS, SCHEMA_PATH, SIMULATED_CLOCK_SKEW_VARIABLE
from controllers import ChannelController, LoginController, PublicationController, ReferenceController
from database import open_database
from models import LogicalClock, PhysicalClock
from repositories import ChannelRepository, LoginRepository, PublicationRepository
from resources import RequestResource
from utils import system_time_ms


def build_request_resource() -> RequestResource:
    server_name = os.environ["SERVER_NAME"]
    database_connection = open_database(DATABASE_PATH, SCHEMA_PATH)
    channel_repository = ChannelRepository(database_connection)
    logical_clock = LogicalClock()
    simulated_clock_skew_ms = int(os.environ.get(SIMULATED_CLOCK_SKEW_VARIABLE, DEFAULT_SIMULATED_CLOCK_SKEW_MS))
    physical_clock = PhysicalClock(simulated_clock_skew_ms, system_time_ms)
    reference_connector = ReferenceConnector(
        os.environ["REFERENCE_ENDPOINT"], server_name, logical_clock, physical_clock
    )
    return RequestResource(
        server_name=server_name,
        broker_connector=BrokerConnector(os.environ["BROKER_SERVER_ENDPOINT"]),
        logical_clock=logical_clock,
        physical_clock=physical_clock,
        login_controller=LoginController(database_connection, LoginRepository(database_connection)),
        channel_controller=ChannelController(database_connection, channel_repository),
        publication_controller=PublicationController(
            database_connection,
            channel_repository,
            PublicationRepository(database_connection),
            ChannelPublisher(os.environ["PROXY_PUBLISHER_ENDPOINT"], logical_clock),
        ),
        reference_controller=ReferenceController(reference_connector, physical_clock),
    )


if __name__ == "__main__":
    build_request_resource().serve_forever()
