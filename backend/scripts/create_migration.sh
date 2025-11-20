#!/bin/bash
# Script to create a new Alembic migration

if [ -z "$1" ]; then
    echo "Usage: ./create_migration.sh \"migration message\""
    exit 1
fi

echo "Creating new migration: $1"
alembic revision --autogenerate -m "$1"
