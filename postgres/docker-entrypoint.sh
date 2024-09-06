#!/bin/bash
set -e

# Function to check if PostgreSQL is ready
pg_isready() {
    PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1
}

# Start PostgreSQL
docker-entrypoint.sh postgres &

# Wait for PostgreSQL to be ready
until pg_isready; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Running migrations..."

# Run migrations
run-migrations.sh

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?

