from enum import StrEnum


class Operation(StrEnum):
    LOGIN = "login"
    CREATE_CHANNEL = "create_channel"
    LIST_CHANNELS = "list_channels"
    PUBLISH = "publish"
    CHANNEL_HISTORY = "channel_history"


class PeerOperation(StrEnum):
    ELECTION = "election"
    CLOCK = "clock"
    REPLICATION_SYNC = "replication_sync"
    REPLICATION_PUSH = "replication_push"


class ReferenceOperation(StrEnum):
    RANK = "rank"
    LIST_SERVERS = "list_servers"
    HEARTBEAT = "heartbeat"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class RecordKind(StrEnum):
    LOGIN = "login"
    CHANNEL = "channel"
    PUBLICATION = "publication"
