from enum import StrEnum


class Operation(StrEnum):
    LOGIN = "login"
    CREATE_CHANNEL = "create_channel"
    LIST_CHANNELS = "list_channels"
    PUBLISH = "publish"


class ReferenceOperation(StrEnum):
    RANK = "rank"
    LIST_SERVERS = "list_servers"
    HEARTBEAT = "heartbeat"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
