from helpers.assertions import setup_succeeded
from helpers.names import new_username
from helpers.protocol import CHANNEL_HISTORY, CREATE_CHANNEL, LIST_CHANNELS, LOGIN, PUBLISH
from helpers.request_exchange import RequestClient


class BbsClient(RequestClient):
    def log_in(self, username: str, timestamp: int | None = None, logical_clock: int | None = None) -> dict:
        return self.exchange_message(self.valid_request(LOGIN, username, {}, timestamp, logical_clock))

    def create_channel(self, channel_name: object, creator_username: str | None = None) -> dict:
        sender = new_username() if creator_username is None else creator_username
        return self.exchange_message(self.valid_request(CREATE_CHANNEL, sender, {"channel": channel_name}))

    def list_channels(self) -> dict:
        return self.exchange_message(self.valid_request(LIST_CHANNELS, new_username(), {}))

    def listed_channel_names(self) -> list[str]:
        return self.list_channels()["payload"]["channels"]

    def publish(
        self,
        channel_name: object,
        message: object,
        author_username: str | None = None,
        timestamp: int | None = None,
        logical_clock: int | None = None,
    ) -> dict:
        sender = new_username() if author_username is None else author_username
        return self.exchange_message(
            self.valid_request(PUBLISH, sender, {"channel": channel_name, "message": message}, timestamp, logical_clock)
        )

    def channel_history(self, channel_name: object) -> dict:
        return self.exchange_message(self.valid_request(CHANNEL_HISTORY, new_username(), {"channel": channel_name}))

    def history_entries(self, channel_name: str) -> list[dict]:
        response = setup_succeeded(self.channel_history(channel_name), "channel history")
        return response["payload"]["publications"]

    def history_messages(self, channel_name: str) -> list[str]:
        return [history_entry["message"] for history_entry in self.history_entries(channel_name)]
