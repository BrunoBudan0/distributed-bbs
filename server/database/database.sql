CREATE TABLE IF NOT EXISTS login (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    logged_in_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS channel (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CONSTRAINT uq_channel_name UNIQUE,
    created_by_username TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL,
    created_logical_clock INTEGER NOT NULL,
    created_on_server TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publication (
    id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL,
    author_username TEXT NOT NULL,
    message TEXT NOT NULL,
    requested_at_ms INTEGER NOT NULL,
    published_at_ms INTEGER NOT NULL,
    published_by_server TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_publication_channel_published_at ON publication (channel_name, published_at_ms);

CREATE TABLE IF NOT EXISTS replicated_record (
    id INTEGER PRIMARY KEY,
    origin_server TEXT NOT NULL,
    origin_sequence INTEGER NOT NULL,
    kind TEXT NOT NULL CONSTRAINT ck_replicated_record_kind CHECK (kind IN ('login', 'channel', 'publication')),
    logical_clock INTEGER NOT NULL,
    content TEXT NOT NULL,
    CONSTRAINT uq_replicated_record_origin UNIQUE (origin_server, origin_sequence)
);
