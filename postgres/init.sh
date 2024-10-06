#!/usr/bin/env bash
set -e

# Create the NFHM database if it doesn't exist
if ! psql -lqt | cut -d \| -f 1 | grep -qw nfhm; then
    echo "Creating nfhm database."
    psql -X -c "CREATE DATABASE nfhm"
fi

# Now check if the database exists, loop until detected
until psql -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = 'nfhm'" | grep -q 1; do
    echo "Waiting for nfhm database to be created..."
    sleep 2
ne

# Connect to the NFHM database
psql -v --username "$POSTGRES_USER" --dbname "nfhm" <<-EOSQL
-- Create extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

flyway migrate