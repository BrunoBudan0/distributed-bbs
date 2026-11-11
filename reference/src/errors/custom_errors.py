from errors.base_error import BbsError


class MalformedMessage(BbsError):
    code = "MALFORMED_MESSAGE"
    description = "the message must be a MessagePack map with operation, sender, timestamp, logical_clock and payload"


class UnknownOperation(BbsError):
    code = "UNKNOWN_OPERATION"
    description = "the operation must be rank, list_servers or heartbeat"


class InvalidServerName(BbsError):
    code = "INVALID_SERVER_NAME"
    description = "the server name must have 1 to 32 letters, digits, underscores or hyphens"


class UnknownServer(BbsError):
    code = "UNKNOWN_SERVER"
    description = "this server never asked for a rank; ask for one before sending heartbeats"
