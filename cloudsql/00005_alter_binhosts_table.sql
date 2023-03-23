ALTER TABLE binhosts
ADD COLUMN IF NOT EXISTS gs_bucket_name TEXT NOT NULL;

INSERT INTO versions (version, name)
VALUES (5, '00005_alter_binhosts_table.sql');