CREATE TABLE IF NOT EXISTS versions
(
    version         INTEGER PRIMARY KEY,
    name            VARCHAR(64),
    timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO versions (version, name)
VALUES (1, '00001_create_versions_table.sql');