#!/usr/bin/env bash
set -e
# -- 1. Create the NFHM database

# drop nfm if already exists
if psql -lqt | cut -d \| -f 1 | grep -qw nfhm; then
    echo "Dropping existing nfhm database."
    psql -X -c "DROP DATABASE nfhm"
fi

psql -X -c "CREATE DATABASE nfhm"

# Now check if the database exists, loop until detected
until psql -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = 'nfhm'" | grep -q 1; do
    echo "Waiting for nfhm database to be created..."
    sleep 2
done

psql -v --username "$POSTGRES_USER" --dbname "nfhm" <<-EOSQL

-- Connect to the NFHM database 
\c nfhm

-- 2. Create the postgis and vector extensions
-- You'll need to make sure you install these extensions ahead of time.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Create the search_records table with the specified schema
-- I (Thomas) kind of guessed at what I think "reasonable" varchar lengths would be.  May need to ammend in the future.
CREATE TABLE search_records (
    id SERIAL PRIMARY KEY,  -- Primary key
    specimen_uuid UUID, -- Can be used to reference the raw data directly in Mongo
    media_uuid UUID, -- Can be used to reference the raw data directly in Mongo (Media records are nested
    collection_date DATE,
    higher_taxon VARCHAR(512),
    common_name VARCHAR(512),
    scientific_name VARCHAR(512),
    recorded_by VARCHAR(256),
    location GEOGRAPHY(POINT),  -- PostGIS geography type for (longitude, latitude)
    tax_kingdom VARCHAR(128),
    tax_phylum VARCHAR(128),
    tax_class VARCHAR(128),
    tax_order VARCHAR(128),
    tax_family VARCHAR(128),
    tax_genus VARCHAR(128),
    catalog_number VARCHAR(128),
    earliest_epoch_or_lowest_series VARCHAR(512),
    earliest_age_or_lowest_stage VARCHAR(512),
    external_media_uri VARCHAR(2083), -- Longest URI supported by most browsers
    embedding VECTOR  -- PGVector extension for storing vector data
);

CREATE UNIQUE INDEX idx_unique_media_uuid ON search_records (media_uuid);

EOSQL
wait 