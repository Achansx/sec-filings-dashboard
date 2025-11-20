# SEC Filings Dashboard - Backend

FastAPI backend service for the SEC Filings Dashboard application.

## Features

- **Async SQLAlchemy** with PostgreSQL for high-performance database operations
- **Alembic migrations** for database schema management
- **Comprehensive data models** for companies, filings, users, and alerts
- **Materialized views** for optimized analytics queries
- **Full test coverage** with pytest and async test support
- **Docker support** for easy deployment

## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic configuration
├── app/
│   ├── api/                 # API endpoints (Phase 1.3)
│   ├── core/                # Core configuration and database
│   │   ├── config.py        # Application settings
│   │   └── database.py      # Database connection and session
│   ├── models/              # SQLAlchemy models
│   │   ├── company.py       # Company model
│   │   ├── filing.py        # Filing and FilingDocument models
│   │   ├── user.py          # User, UserAlert, AlertMatch models
│   │   └── audit.py         # AuditLog model
│   ├── schemas/             # Pydantic schemas (Phase 1.3)
│   ├── services/            # Business logic (Phase 2+)
│   ├── tasks/               # Celery tasks (Phase 2+)
│   └── main.py              # FastAPI application entry point
├── scripts/                 # Helper scripts
│   ├── migrate.sh           # Run database migrations
│   ├── create_migration.sh  # Create new migration
│   └── reset_db.sh          # Reset database (WARNING: destroys data)
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest configuration and fixtures
│   └── test_models.py       # Model tests
├── alembic.ini              # Alembic configuration file
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
└── Dockerfile               # Docker image definition
```

## Database Schema

### Tables

- **companies**: SEC registered companies (CIK, name, ticker, etc.)
- **filings**: SEC filings (10-K, 10-Q, 8-K, etc.)
- **filing_documents**: Individual documents within filings
- **users**: Application users (OAuth authentication)
- **user_alerts**: User-configured alerts for filings
- **alert_matches**: Alert match tracking and notifications
- **audit_logs**: Audit log for user actions

### Materialized Views

- **company_filing_stats**: Aggregated filing counts by company
- **monthly_filing_stats**: Monthly filing statistics by form type

## Setup

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp ../.env.example ../.env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL** (via docker-compose from project root):
   ```bash
   docker-compose up -d postgres
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - OpenAPI: http://localhost:8000/redoc

### Docker

Run the entire stack with docker-compose from the project root:

```bash
docker-compose up
```

## Database Migrations

### Apply migrations

```bash
alembic upgrade head
```

### Create a new migration

```bash
./scripts/create_migration.sh "description of changes"
```

### Rollback last migration

```bash
alembic downgrade -1
```

### Reset database (WARNING: destroys all data)

```bash
./scripts/reset_db.sh
```

### View migration history

```bash
alembic history
```

### View current version

```bash
alembic current
```

## Testing

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=app --cov-report=html
```

### Run specific test file

```bash
pytest tests/test_models.py
```

### Run with verbose output

```bash
pytest -v
```

## Database Connection

The application uses async SQLAlchemy with the following configuration:

- **Pool size**: 20 connections
- **Max overflow**: 10 connections
- **Pool timeout**: 30 seconds
- **Pool recycle**: 3600 seconds (1 hour)
- **Pre-ping**: Enabled (verifies connections before use)

## Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ELASTICSEARCH_URL`: Elasticsearch connection string
- `SECRET_KEY`: Application secret key
- `ENVIRONMENT`: Environment (development/staging/production)
- `DEBUG`: Enable debug mode (True/False)

## API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Phase 1.2 Status ✅

Phase 1.2 (Database Schema & Migrations) is **COMPLETE**:

- ✅ Alembic initialized with async support
- ✅ SQLAlchemy configured with connection pooling
- ✅ All 7 data models created with proper relationships
- ✅ Comprehensive indexes for query performance
- ✅ Materialized views for analytics
- ✅ Test database configuration
- ✅ Full migration system operational

## Next Steps (Phase 1.3)

- Create Pydantic schemas for request/response validation
- Implement API endpoints for CRUD operations
- Add authentication middleware
- Create API documentation

## License

Copyright © 2025 SEC Filings Dashboard
