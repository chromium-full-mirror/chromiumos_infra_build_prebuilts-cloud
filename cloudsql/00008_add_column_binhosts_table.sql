ALTER TABLE binhosts
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

INSERT INTO versions (version, name)
VALUES (8, '00008_add_column_binhosts_table.sql');