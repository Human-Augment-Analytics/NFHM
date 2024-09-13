-- 1. Add new columns
ALTER TABLE search_records
ADD COLUMN model VARCHAR(255),
ADD COLUMN pretrained VARCHAR(255),
ADD COLUMN embed_version VARCHAR(512);

-- 2. Backfill existing rows with default OpenClip values we've been using
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

-- 5. Create a separate index for embed_version
CREATE INDEX idx_embed_version ON search_records (embed_version);

-- Add NOT NULL constraints to the new columns for data integrity
ALTER TABLE search_records
ALTER COLUMN model SET NOT NULL,
ALTER COLUMN pretrained SET NOT NULL,
ALTER COLUMN embed_version SET NOT NULL;