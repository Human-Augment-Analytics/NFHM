#!/bin/bash
set -e

# Function to check if PostgreSQL is ready
pg_isready() {
    PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1
}

# Start PostgreSQL
/usr/local/bin/docker-entrypoint.sh postgres &

# Wait for PostgreSQL to be ready
until pg_isready; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Creating extensions..."

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "Extensions created. Running Flyway migrations..."

# Run Flyway migrations with baseline
flyway -url=jdbc:postgresql://localhost:5432/$POSTGRES_DB -user=$POSTGRES_USER -password=$POSTGRES_PASSWORD -baselineOnMigrate=true -locations=filesystem:/flyway/sql migrate

echo "Flyway migrations completed."

# Keep the container running
wait
