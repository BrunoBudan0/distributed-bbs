import os

from connectors import (
    BrokerConnector,
    ChannelPublisher,
    IncomingPoller,
    PeerConnector,
    PeerServerConnector,
    ReferenceConnector,
    ServerTopicSubscriber,
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
    ReplicationController,
    ReplicationLog,
)
from database import open_database
from models import BerkeleyCoordinator, LogicalClock, PhysicalClock
from repositories import ChannelRepository, LoginRepository, PublicationRepository, ReplicationRepository
from resources import PeerResource, RequestResource, ServerLoop, ServerTopicResource
from utils import system_time_ms


def build_server_loop() -> ServerLoop:
    server_name = os.environ["SERVER_NAME"]
    database_connection = open_database(DATABASE_PATH, SCHEMA_PATH)
    login_repository = LoginRepository(database_connection)
    channel_repository = ChannelRepository(database_connection)
    publication_repository = PublicationRepository(database_connection)
    replication_repository = ReplicationRepository(database_connection)
    logical_clock = LogicalClock()
    simulated_clock_skew_ms = int(os.environ.get(SIMULATED_CLOCK_SKEW_VARIABLE, DEFAULT_SIMULATED_CLOCK_SKEW_MS))
    physical_clock = PhysicalClock(simulated_clock_skew_ms, system_time_ms)

    broker_connector = BrokerConnector(os.environ["BROKER_SERVER_ENDPOINT"])
    peer_server_connector = PeerServerConnector()
    server_topic_subscriber = ServerTopicSubscriber(os.environ["PROXY_SUBSCRIBER_ENDPOINT"])
    channel_publisher = ChannelPublisher(os.environ["PROXY_PUBLISHER_ENDPOINT"], logical_clock)
    peer_connector = PeerConnector(server_name, logical_clock, physical_clock)
    replication_log = ReplicationLog(
        server_name, replication_repository, channel_publisher, logical_clock, physical_clock
    )

    reference_controller = ReferenceController(
        ReferenceConnector(os.environ["REFERENCE_ENDPOINT"], server_name, logical_clock, physical_clock)
    )
    coordination_controller = CoordinationController(
        server_name,
        reference_controller,
        peer_connector,
        channel_publisher,
        physical_clock,
        BerkeleyCoordinator(BERKELEY_READING_VALIDITY_MS),
    )
    replication_controller = ReplicationController(
        server_name,
        database_connection,
        replication_repository,
        login_repository,
        channel_repository,
        publication_repository,
        peer_connector,
    )

    return ServerLoop(
        incoming_poller=IncomingPoller(broker_connector, peer_server_connector, server_topic_subscriber),
        request_resource=RequestResource(
            server_name,
            broker_connector,
            logical_clock,
            physical_clock,
            LoginController(database_connection, login_repository, replication_log),
            ChannelController(database_connection, channel_repository, replication_log),
            PublicationController(
                database_connection, channel_repository, publication_repository, channel_publisher, replication_log
            ),
        ),
        peer_resource=PeerResource(
            server_name,
            peer_server_connector,
            logical_clock,
            physical_clock,
            coordination_controller,
            replication_controller,
        ),
        server_topic_resource=ServerTopicResource(
            server_name, server_topic_subscriber, logical_clock, coordination_controller, replication_controller
        ),
        reference_controller=reference_controller,
        coordination_controller=coordination_controller,
        replication_controller=replication_controller,
    )


if __name__ == "__main__":
    build_server_loop().run_forever()
