-- 1. Add new columns
ALTER TABLE search_records
ADD COLUMN model VARCHAR(255),
ADD COLUMN pretrained VARCHAR(255),
ADD COLUMN embed_version VARCHAR(512);

-- 2. Backfill existing rows
UPDATE search_records
SET model = 'ViT-B-32',
    pretrained = 'laion2b_s34b_b79k',
    embed_version = 'default'
WHERE model IS NULL;

-- 3. Drop the existing unique index
DROP INDEX IF EXISTS idx_unique_media_uuid;

-- 4. Create new unique index on media_uuid and embed_version
CREATE UNIQUE INDEX idx_unique_media_uuid_embed_version 
ON search_records (media_uuid, embed_version);

-- 5. Create an index for similarity search on embedding, filtered by embed_version
-- Note: This assumes 'embedding' is of type vector. Vector dimension is specific to
-- model so we may need to reqthink how this works with the different models we explore . . .https://arxiv.org/pdf/2103.00020
CREATE INDEX idx_embedding_embed_version ON search_records 
USING ivfflat (embedding vector_l2_ops, embed_version)
WITH (lists = 100);  -- Adjust the number of lists based on your data size and query patterns.  Not super sure about this yet

-- Optionally, you might want to add NOT NULL constraints to the new columns
ALTER TABLE search_records
ALTER COLUMN model SET NOT NULL,
ALTER COLUMN pretrained SET NOT NULL,
ALTER COLUMN embed_version SET NOT NULL;
