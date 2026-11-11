from enum import StrEnum


class Operation(StrEnum):
    RANK = "rank"
    LIST_SERVERS = "list_servers"
    HEARTBEAT = "heartbeat"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
