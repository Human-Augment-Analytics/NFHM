-- 1. Create the NFHM database
CREATE DATABASE NFHM;

-- Connect to the NFHM database 
\c NFHM

-- 2. Create the postgis and vector extensions
-- You'll need to make sure you install these extensions ahead of time.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Create the search_records table with the specified schema
-- I (Thomas) kind of guessed at what I think "reasonable" varchar lengths would be.  May need to ammend in the future.
CREATE TABLE search_records (
    id SERIAL PRIMARY KEY,
    specimen_uuid uuid, -- Can be used to reference raw data in MongoDB
    media_uuid uuid, -- Can be used to reference raw data in MongoDB in the nested media records
    collectiondate date,
    highertaxon character varying(128),
    commonname character varying(512),
    scientificname character varying(512),
    recordedby character varying(256),
    location geography(Point,4326), -- PostGIS geography type for (longitude, latitude)
    tax_kingdom character varying(128),
    tax_phylum character varying(128),
    tax_class character varying(128),
    tax_order character varying(128),
    tax_family character varying(128),
    tax_genus character varying(128),
    catalognumber character varying(128),
    earliest_epoch_or_lowest_series character varying(128),
    earliest_age_or_lowest_stage character varying(512),
    external_media_uri character varying(2083),
    embedding vector -- PGVector extension for storing vector data
);

