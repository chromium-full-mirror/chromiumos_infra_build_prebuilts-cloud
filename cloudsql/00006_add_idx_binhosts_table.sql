CREATE INDEX binhosts_snapshot_sha_idx ON binhosts (snapshot_sha);
CREATE UNIQUE INDEX binhosts_gs_uri_unique_idx ON binhosts (gs_uri);

INSERT INTO versions (version, name)
VALUES (6, '00006_add_idx_binhosts_table.sql');