#!/bin/bash
# Script to reset database (WARNING: Destroys all data!)

set -e

echo "WARNING: This will destroy all data in the database!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Downgrading database..."
alembic downgrade base

echo "Upgrading database..."
alembic upgrade head

echo "Database reset complete!"
