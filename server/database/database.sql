CREATE TABLE IF NOT EXISTS login (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    logged_in_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS channel (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CONSTRAINT uq_channel_name UNIQUE,
    created_by_username TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS publication (
    id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL CONSTRAINT fk_publication_channel REFERENCES channel (name),
    author_username TEXT NOT NULL,
    message TEXT NOT NULL,
    requested_at_ms INTEGER NOT NULL,
    published_at_ms INTEGER NOT NULL,
    published_by_server TEXT NOT NULL
);
