#!/bin/bash
# Database migration script

set -e

echo "Running database migrations..."

# Wait for database to be ready
echo "Waiting for database..."
while ! PGPASSWORD=$POSTGRES_PASSWORD psql -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-secfilings} -d ${POSTGRES_DB:-secfilings} -c '\q' 2>/dev/null; do
    sleep 1
done

echo "Database is ready!"

# Run migrations
alembic upgrade head

echo "Migrations completed successfully!"
