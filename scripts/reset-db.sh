#!/bin/bash

# SEC Filings Dashboard - Database Reset Script
# WARNING: This script will DROP and RECREATE the database
# All data will be lost!

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Load environment variables
if [ -f .env ]; then
    source .env
else
    print_error ".env file not found!"
    exit 1
fi

# Set default values if not in .env
POSTGRES_USER=${POSTGRES_USER:-secfilings}
POSTGRES_DB=${POSTGRES_DB:-secfilings}

print_header "Database Reset Utility"

print_warning "⚠️  WARNING: This will DELETE ALL DATA in the database!"
print_warning "⚠️  Database: $POSTGRES_DB"
print_warning "⚠️  User: $POSTGRES_USER"
echo ""

# Ask for confirmation
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

if [ "$confirmation" != "yes" ]; then
    print_info "Database reset cancelled."
    exit 0
fi

echo ""
print_info "Starting database reset..."

# Step 1: Check if PostgreSQL container is running
print_info "Checking PostgreSQL container..."

if ! docker-compose ps postgres | grep -q "Up"; then
    print_error "PostgreSQL container is not running!"
    print_info "Starting PostgreSQL container..."
    docker-compose up -d postgres

    # Wait for PostgreSQL to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 5

    max_attempts=30
    attempt=0
    while ! docker-compose exec -T postgres pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            print_error "PostgreSQL failed to start after $max_attempts attempts"
            exit 1
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    print_success "PostgreSQL is ready"
else
    print_success "PostgreSQL container is running"
fi

# Step 2: Terminate active connections
print_info "Terminating active database connections..."

docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres << EOF > /dev/null 2>&1 || true
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$POSTGRES_DB'
  AND pid <> pg_backend_pid();
EOF

print_success "Active connections terminated"

# Step 3: Drop the database
print_info "Dropping database '$POSTGRES_DB'..."

docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres << EOF
DROP DATABASE IF EXISTS $POSTGRES_DB;
EOF

print_success "Database dropped"

# Step 4: Create the database
print_info "Creating database '$POSTGRES_DB'..."

docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres << EOF
CREATE DATABASE $POSTGRES_DB;
EOF

print_success "Database created"

# Step 5: Create extensions (if needed)
print_info "Creating database extensions..."

docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOF

print_success "Extensions created"

# Step 6: Run migrations (if Alembic is set up)
if [ -d "backend/alembic" ]; then
    print_info "Running database migrations..."

    # Check if API container is running
    if docker-compose ps api | grep -q "Up"; then
        docker-compose exec -T api alembic upgrade head
        print_success "Migrations applied"
    else
        print_warning "API container is not running. Skipping migrations."
        print_info "Start the API container and run: docker-compose exec api alembic upgrade head"
    fi
else
    print_warning "Alembic migrations not found. Skipping migrations."
fi

# Step 7: Clear Redis cache
print_info "Clearing Redis cache..."

if docker-compose ps redis | grep -q "Up"; then
    REDIS_PASSWORD=${REDIS_PASSWORD:-redis_dev_password}
    docker-compose exec -T redis redis-cli -a "$REDIS_PASSWORD" FLUSHALL > /dev/null 2>&1 || true
    print_success "Redis cache cleared"
else
    print_warning "Redis container is not running. Skipping cache clear."
fi

# Step 8: Clear Elasticsearch indexes
print_info "Clearing Elasticsearch indexes..."

if docker-compose ps elasticsearch | grep -q "Up"; then
    # Wait for Elasticsearch to be ready
    max_attempts=30
    attempt=0
    while ! curl -sf http://localhost:9200/_cluster/health > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            print_warning "Elasticsearch is not responding. Skipping index cleanup."
            break
        fi
        sleep 1
    done

    if [ $attempt -lt $max_attempts ]; then
        # Delete all indexes starting with the prefix
        ES_INDEX_PREFIX=${ELASTICSEARCH_INDEX_PREFIX:-sec_filings}
        curl -sf -X DELETE "http://localhost:9200/${ES_INDEX_PREFIX}_*" > /dev/null 2>&1 || true
        print_success "Elasticsearch indexes cleared"
    fi
else
    print_warning "Elasticsearch container is not running. Skipping index cleanup."
fi

print_header "Database Reset Complete!"

print_success "Database has been reset successfully"
echo ""
print_info "Next steps:"
echo "  1. Run migrations if not done: docker-compose exec api alembic upgrade head"
echo "  2. Seed test data: ./scripts/seed-data.sh"
echo "  3. Restart services: docker-compose restart"
echo ""
