-- Index names should follow the pattern <db_name>_<field_names>_<unique?>_idx
-- but this does not have field names in it because it becomes too long and the
-- build_target_profiles table will only have this unique index.
CREATE UNIQUE INDEX build_target_profiles_unique_idx
ON build_target_profiles (build_target, profile);

INSERT INTO versions (version, name)
VALUES (7, '00007_add_idx_build_target_profiles_table.sql');