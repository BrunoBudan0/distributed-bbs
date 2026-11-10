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
