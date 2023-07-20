ALTER TABLE snapshots
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

INSERT INTO versions (version, name)
VALUES (9, '00009_add_column_snapshots_table.sql');