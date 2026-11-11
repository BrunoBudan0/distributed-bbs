import os

from connectors import (
    BrokerConnector,
    ChannelPublisher,
    CoordinatorSubscriber,
    IncomingPoller,
    PeerConnector,
    PeerServerConnector,
    ReferenceConnector,
)
from constants import (
    BERKELEY_READING_VALIDITY_MS,
    DATABASE_PATH,
    DEFAULT_SIMULATED_CLOCK_SKEW_MS,
    SCHEMA_PATH,
    SIMULATED_CLOCK_SKEW_VARIABLE,
)
from controllers import (
    ChannelController,
    CoordinationController,
    LoginController,
    PublicationController,
    ReferenceController,
)
from database import open_database
from models import BerkeleyCoordinator, LogicalClock, PhysicalClock
from repositories import ChannelRepository, LoginRepository, PublicationRepository
from resources import AnnouncementResource, PeerResource, RequestResource, ServerLoop
from utils import system_time_ms


def build_server_loop() -> ServerLoop:
    server_name = os.environ["SERVER_NAME"]
    database_connection = open_database(DATABASE_PATH, SCHEMA_PATH)
    channel_repository = ChannelRepository(database_connection)
    logical_clock = LogicalClock()
    simulated_clock_skew_ms = int(os.environ.get(SIMULATED_CLOCK_SKEW_VARIABLE, DEFAULT_SIMULATED_CLOCK_SKEW_MS))
    physical_clock = PhysicalClock(simulated_clock_skew_ms, system_time_ms)

    broker_connector = BrokerConnector(os.environ["BROKER_SERVER_ENDPOINT"])
    peer_server_connector = PeerServerConnector()
    coordinator_subscriber = CoordinatorSubscriber(os.environ["PROXY_SUBSCRIBER_ENDPOINT"])
    channel_publisher = ChannelPublisher(os.environ["PROXY_PUBLISHER_ENDPOINT"], logical_clock)

    reference_controller = ReferenceController(
        ReferenceConnector(os.environ["REFERENCE_ENDPOINT"], server_name, logical_clock, physical_clock)
    )
    coordination_controller = CoordinationController(
        server_name,
        reference_controller,
        PeerConnector(server_name, logical_clock, physical_clock),
        channel_publisher,
        physical_clock,
        BerkeleyCoordinator(BERKELEY_READING_VALIDITY_MS),
    )

    return ServerLoop(
        incoming_poller=IncomingPoller(broker_connector, peer_server_connector, coordinator_subscriber),
        request_resource=RequestResource(
            server_name,
            broker_connector,
            logical_clock,
            physical_clock,
            LoginController(database_connection, LoginRepository(database_connection)),
            ChannelController(database_connection, channel_repository),
            PublicationController(
                database_connection, channel_repository, PublicationRepository(database_connection), channel_publisher
            ),
        ),
        peer_resource=PeerResource(
            server_name, peer_server_connector, logical_clock, physical_clock, coordination_controller
        ),
        announcement_resource=AnnouncementResource(coordinator_subscriber, logical_clock, coordination_controller),
        reference_controller=reference_controller,
        coordination_controller=coordination_controller,
    )


if __name__ == "__main__":
    build_server_loop().run_forever()
