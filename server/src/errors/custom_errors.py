from errors.base_error import BbsError


class MalformedMessage(BbsError):
    code = "MALFORMED_MESSAGE"
    description = "the message must be a MessagePack map with operation, sender, timestamp, logical_clock and payload"


class UnknownOperation(BbsError):
    code = "UNKNOWN_OPERATION"
    description = "the operation must be login, create_channel, list_channels, publish or channel_history"


class UnknownPeerOperation(BbsError):
    code = "UNKNOWN_OPERATION"
    description = "the operation between servers must be election, clock, replication_sync or replication_push"


class InvalidReplicatedRecord(BbsError):
    code = "INVALID_RECORD"
    description = "every replicated record needs a valid origin, a sequence from 1, a known kind and a valid content"


class InvalidUsername(BbsError):
    code = "INVALID_USERNAME"
    description = "the username must have 1 to 32 letters, digits, underscores or hyphens"


class InvalidServerName(BbsError):
    code = "INVALID_SERVER_NAME"
    description = "the server name must have 1 to 32 letters, digits, underscores or hyphens"


class InvalidChannelName(BbsError):
    code = "INVALID_CHANNEL_NAME"
    description = (
        "the channel name must have 1 to 32 lowercase letters, digits or hyphens and cannot be 'servers' or 'replication'"
    )


class ChannelAlreadyExists(BbsError):
    code = "CHANNEL_ALREADY_EXISTS"
    description = "a channel with this name already exists on this server"


class ChannelNotFound(BbsError):
    code = "CHANNEL_NOT_FOUND"
    description = "there is no channel with this name on this server"


class InvalidMessage(BbsError):
    code = "INVALID_MESSAGE"
    description = "the message must be a text with 1 to 500 characters"


class NotCoordinator(BbsError):
    code = "NOT_COORDINATOR"
    description = "this server is not the coordinator; ask the elected coordinator for the clock"
