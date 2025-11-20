#!/bin/bash

# SEC Filings Dashboard - Development Setup Script
# This script sets up the development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup process
main() {
    print_header "SEC Filings Dashboard - Development Setup"

    # Step 1: Check prerequisites
    print_info "Checking prerequisites..."

    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    print_success "Docker is installed"

    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    print_success "Docker Compose is installed"

    # Step 2: Check for .env file
    print_header "Environment Configuration"

    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "IMPORTANT: Please edit .env and configure required variables:"
        print_info "  - SEC_API_USER_AGENT (required by SEC)"
        print_info "  - SECRET_KEY (generate with: openssl rand -hex 32)"
        print_info "  - OAuth credentials (if using authentication)"
        echo ""
        read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
    else
        print_success ".env file exists"
    fi

    # Step 3: Validate critical environment variables
    print_info "Validating environment variables..."

    source .env 2>/dev/null || true

    if [ -z "$SEC_API_USER_AGENT" ] || [ "$SEC_API_USER_AGENT" = "YourCompanyName YourName (your.email@example.com)" ]; then
        print_error "SEC_API_USER_AGENT is not configured in .env"
        print_info "SEC requires a User-Agent header with your contact information"
        print_info "Example: 'MyCompany John Doe (john@example.com)'"
        exit 1
    fi
    print_success "SEC_API_USER_AGENT is configured"

    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here-change-in-production-min-32-chars" ]; then
        print_warning "SECRET_KEY is using default value"
        print_info "Generating a new SECRET_KEY..."
        if command_exists openssl; then
            NEW_SECRET=$(openssl rand -hex 32)
            # Update .env file
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
            else
                sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
            fi
            print_success "SECRET_KEY generated and updated in .env"
        else
            print_warning "openssl not found. Please manually set SECRET_KEY in .env"
        fi
    else
        print_success "SECRET_KEY is configured"
    fi

    # Step 4: Create necessary directories
    print_header "Creating Directory Structure"

    mkdir -p backend/logs
    mkdir -p backend/storage
    mkdir -p backend/init-scripts
    mkdir -p frontend
    mkdir -p scripts

    print_success "Directories created"

    # Step 5: Stop any running containers
    print_header "Cleaning Up Existing Containers"

    print_info "Stopping any running containers..."
    docker-compose down 2>/dev/null || true
    print_success "Cleanup complete"

    # Step 6: Pull Docker images
    print_header "Pulling Docker Images"

    print_info "This may take a few minutes on first run..."
    docker-compose pull postgres redis elasticsearch
    print_success "Base images pulled"

    # Step 7: Create initial backend structure
    print_header "Creating Backend Structure"

    if [ ! -d "backend/app" ]; then
        print_info "Creating backend application structure..."
        mkdir -p backend/app/{api/v1,models,schemas,services,workers}
        touch backend/app/__init__.py
        touch backend/app/main.py
        touch backend/app/config.py
        touch backend/app/database.py
        touch backend/app/dependencies.py

        # Create __init__.py files
        find backend/app -type d -exec touch {}/__init__.py \;

        print_success "Backend structure created"
    else
        print_success "Backend structure already exists"
    fi

    # Step 8: Create initial frontend structure
    print_header "Creating Frontend Structure"

    if [ ! -d "frontend/pages" ]; then
        print_info "Creating frontend application structure..."
        mkdir -p frontend/{pages,components,lib,hooks,styles,public}

        print_success "Frontend structure created"
    else
        print_success "Frontend structure already exists"
    fi

    # Step 9: Create backend Dockerfile if it doesn't exist
    print_header "Creating Dockerfiles"

    if [ ! -f "backend/Dockerfile" ]; then
        print_info "Creating backend Dockerfile..."
        cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Development target
FROM base as development
RUN pip install --no-cache-dir watchdog pytest pytest-cov
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production target
FROM base as production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
        print_success "Backend Dockerfile created"
    else
        print_success "Backend Dockerfile already exists"
    fi

    if [ ! -f "frontend/Dockerfile" ]; then
        print_info "Creating frontend Dockerfile..."
        cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine as base

WORKDIR /app

COPY package*.json ./

# Development target
FROM base as development
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

# Production target
FROM base as production
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
EOF
        print_success "Frontend Dockerfile created"
    else
        print_success "Frontend Dockerfile already exists"
    fi

    # Step 10: Create backend requirements.txt if it doesn't exist
    if [ ! -f "backend/requirements.txt" ]; then
        print_info "Creating backend requirements.txt..."
        cat > backend/requirements.txt << 'EOF'
# FastAPI and ASGI server
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
psycopg2-binary==2.9.9

# Redis
redis==5.0.1
hiredis==2.2.3

# Elasticsearch
elasticsearch==8.11.0

# Celery for background tasks
celery==5.3.4

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# HTTP client
httpx==0.25.2
aiohttp==3.9.1

# Validation
pydantic==2.5.2
pydantic-settings==2.1.0
email-validator==2.1.0

# Date/Time
python-dateutil==2.8.2

# Utilities
python-slugify==8.0.1

# SEC EDGAR
sec-edgar-downloader==5.0.3

# Email
sendgrid==6.11.0

# AI/ML (optional)
openai==1.3.8
anthropic==0.7.7
EOF
        print_success "Backend requirements.txt created"
    else
        print_success "Backend requirements.txt already exists"
    fi

    # Step 11: Create frontend package.json if it doesn't exist
    if [ ! -f "frontend/package.json" ]; then
        print_info "Creating frontend package.json..."
        cat > frontend/package.json << 'EOF'
{
  "name": "sec-filings-dashboard-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "20.10.0",
    "@types/react": "18.2.42",
    "@types/react-dom": "18.2.17",
    "eslint": "8.54.0",
    "eslint-config-next": "14.0.3",
    "typescript": "5.3.2"
  }
}
EOF
        print_success "Frontend package.json created"
    else
        print_success "Frontend package.json already exists"
    fi

    # Final message
    print_header "Setup Complete!"

    print_success "Development environment is ready!"
    echo ""
    print_info "Next steps:"
    echo "  1. Review and customize .env if needed"
    echo "  2. Start services: docker-compose up"
    echo "  3. Access the application:"
    echo "     - Frontend: http://localhost:3000"
    echo "     - API Docs: http://localhost:8000/docs"
    echo "     - PostgreSQL: localhost:5432"
    echo "     - Elasticsearch: http://localhost:9200"
    echo "     - Redis: localhost:6379"
    echo ""
    print_info "Useful commands:"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Stop services: docker-compose down"
    echo "  - Reset database: ./scripts/reset-db.sh"
    echo "  - Seed data: ./scripts/seed-data.sh"
    echo ""
}

# Run main function
main "$@"
