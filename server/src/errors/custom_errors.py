from errors.base_error import BbsError


class MalformedMessage(BbsError):
    code = "MALFORMED_MESSAGE"
    description = "the message must be a MessagePack map with operation, sender, timestamp, logical_clock and payload"


class UnknownOperation(BbsError):
    code = "UNKNOWN_OPERATION"
    description = "the operation must be login, create_channel, list_channels or publish"


class InvalidUsername(BbsError):
    code = "INVALID_USERNAME"
    description = "the username must have 1 to 32 letters, digits, underscores or hyphens"


class InvalidChannelName(BbsError):
    code = "INVALID_CHANNEL_NAME"
    description = "the channel name must have 1 to 32 lowercase letters, digits or hyphens"


class ChannelAlreadyExists(BbsError):
    code = "CHANNEL_ALREADY_EXISTS"
    description = "a channel with this name already exists on this server"


class ChannelNotFound(BbsError):
    code = "CHANNEL_NOT_FOUND"
    description = "there is no channel with this name on this server"


class InvalidMessage(BbsError):
    code = "INVALID_MESSAGE"
    description = "the message must be a text with 1 to 500 characters"
