-- 1. Create the search_records table with the specified schema
CREATE TABLE IF NOT EXISTS search_records (
    id SERIAL PRIMARY KEY,
    specimen_uuid UUID,
    media_uuid UUID,
    collection_date DATE,
    higher_taxon VARCHAR(512),
    common_name VARCHAR(512),
    scientific_name VARCHAR(512),
    recorded_by VARCHAR(256),
    location GEOGRAPHY(POINT),
    tax_kingdom VARCHAR(128),
    tax_phylum VARCHAR(128),
    tax_class VARCHAR(128),
    tax_order VARCHAR(128),
    tax_family VARCHAR(128),
    tax_genus VARCHAR(128),
    catalog_number VARCHAR(128),
    earliest_epoch_or_lowest_series VARCHAR(512),
    earliest_age_or_lowest_stage VARCHAR(512),
    external_media_uri VARCHAR(2083),
    embedding VECTOR
);

-- 2. Create unique index
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_media_uuid ON search_records (media_uuid);


