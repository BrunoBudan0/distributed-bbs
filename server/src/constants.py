import re
from pathlib import Path

DATABASE_PATH = Path("/data/bbs.sqlite3")
SCHEMA_PATH = Path(__file__).parent.parent / "database" / "database.sql"

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,32}")
CHANNEL_NAME_PATTERN = re.compile(r"[a-z0-9-]{1,32}")

MIN_TIMESTAMP_MS = 0
MAX_TIMESTAMP_MS = 253402300799999

MIN_MESSAGE_LENGTH = 1
MAX_MESSAGE_LENGTH = 500

OPERATION_FIELD = "operation"
SENDER_FIELD = "sender"
TIMESTAMP_FIELD = "timestamp"
PAYLOAD_FIELD = "payload"
STATUS_FIELD = "status"
CHANNEL_FIELD = "channel"
CHANNELS_FIELD = "channels"
MESSAGE_FIELD = "message"
AUTHOR_FIELD = "author"
ERROR_CODE_FIELD = "error_code"
ERROR_DESCRIPTION_FIELD = "error_description"

UNIDENTIFIED_OPERATION = "unidentified"
PUBLICATION_OPERATION = "publication"
