CREATE TABLE IF NOT EXISTS snapshots
(
    snapshot_sha    VARCHAR(40) PRIMARY KEY,
    snapshot_num    INT NOT NULL,
    external        BOOLEAN NOT NULL,
    buildbucket_id  BIGINT NOT NULL
);

INSERT INTO versions (version, name)
VALUES (2, '00002_create_snapshots_table.sql');