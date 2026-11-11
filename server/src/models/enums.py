from enum import StrEnum


class Operation(StrEnum):
    LOGIN = "login"
    CREATE_CHANNEL = "create_channel"
    LIST_CHANNELS = "list_channels"
    PUBLISH = "publish"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
