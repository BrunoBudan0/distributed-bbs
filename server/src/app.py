import os

from connectors import BrokerConnector, ChannelPublisher
from constants import DATABASE_PATH, SCHEMA_PATH
from controllers import ChannelController, LoginController, PublicationController
from database import open_database
from repositories import ChannelRepository, LoginRepository, PublicationRepository
from resources import RequestResource


def build_request_resource() -> RequestResource:
    database_connection = open_database(DATABASE_PATH, SCHEMA_PATH)
    channel_repository = ChannelRepository(database_connection)
    return RequestResource(
        server_name=os.environ["SERVER_NAME"],
        broker_connector=BrokerConnector(os.environ["BROKER_SERVER_ENDPOINT"]),
        login_controller=LoginController(database_connection, LoginRepository(database_connection)),
        channel_controller=ChannelController(database_connection, channel_repository),
        publication_controller=PublicationController(
            database_connection,
            channel_repository,
            PublicationRepository(database_connection),
            ChannelPublisher(os.environ["PROXY_PUBLISHER_ENDPOINT"]),
        ),
    )


if __name__ == "__main__":
    build_request_resource().serve_forever()
