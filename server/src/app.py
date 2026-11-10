import os

from connectors import BrokerConnector
from constants import DATABASE_PATH, SCHEMA_PATH
from controllers import ChannelController, LoginController
from database import open_database
from repositories import ChannelRepository, LoginRepository
from resources import RequestResource


def build_request_resource() -> RequestResource:
    database_connection = open_database(DATABASE_PATH, SCHEMA_PATH)
    return RequestResource(
        server_name=os.environ["SERVER_NAME"],
        broker_connector=BrokerConnector(os.environ["BROKER_SERVER_ENDPOINT"]),
        login_controller=LoginController(database_connection, LoginRepository(database_connection)),
        channel_controller=ChannelController(database_connection, ChannelRepository(database_connection)),
    )


if __name__ == "__main__":
    build_request_resource().serve_forever()
