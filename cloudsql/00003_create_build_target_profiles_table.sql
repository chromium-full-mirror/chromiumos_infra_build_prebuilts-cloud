CREATE TABLE IF NOT EXISTS build_target_profiles
(
    build_target_profile_id     SERIAL PRIMARY KEY,
    build_target                VARCHAR(128) NOT NULL,
    profile                     VARCHAR(128) NOT NULL
);

INSERT INTO versions (version, name)
VALUES (3, '00003_create_build_target_profiles_table.sql');