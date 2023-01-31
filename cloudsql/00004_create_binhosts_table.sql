CREATE TABLE IF NOT EXISTS binhosts
(
    binhost_id                  BIGSERIAL PRIMARY KEY,
    build_target_profile_id     INTEGER NOT NULL REFERENCES build_target_profiles,
    snapshot_sha                VARCHAR(40) REFERENCES snapshots,
    gs_uri                      TEXT NOT NULL,
    buildbucket_id              BIGINT NOT NULL,
    complete                    BOOLEAN NOT NULL DEFAULT TRUE,
    private                     BOOLEAN NOT NULL,
    last_accessed               TIMESTAMP
);

INSERT INTO versions (version, name)
VALUES (4, '00004_create_binhosts_table.sql');