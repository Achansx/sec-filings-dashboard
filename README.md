# SEC Filings Dashboard

A comprehensive platform for monitoring, analyzing, and receiving alerts on SEC EDGAR filings. Built with FastAPI, React/Next.js, PostgreSQL, Elasticsearch, and Redis.

## Features

- **Real-time Filing Monitoring**: Automatically sync and index SEC filings
- **Full-text Search**: Powerful search across all filing documents using Elasticsearch
- **Custom Alerts**: Set up personalized alerts based on companies, form types, and keywords
- **AI-Powered Summaries**: Get AI-generated summaries of complex filings
- **Export Capabilities**: Export data to PDF, Excel, and CSV formats
- **OAuth Authentication**: Secure login with Google and GitHub
- **RESTful API**: Well-documented API for programmatic access

## Architecture

```
sec-filings-dashboard/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── workers/     # Background tasks
│   ├── alembic/         # Database migrations
│   └── tests/           # Backend tests
├── frontend/            # Next.js application
│   ├── components/      # React components
│   ├── pages/          # Next.js pages
│   ├── hooks/          # Custom React hooks
│   └── lib/            # Utilities
├── scripts/            # Development scripts
└── docker-compose.yml  # Docker services
```

## Prerequisites

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Git** (v2.30+)
- **Node.js** (v18+) - for local frontend development
- **Python** (v3.11+) - for local backend development
- **SEC API User Agent**: You'll need to provide your contact information for SEC API access

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sec-filings-dashboard.git
cd sec-filings-dashboard
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and update the following **required** variables:

```bash
# IMPORTANT: SEC requires your contact info
SEC_API_USER_AGENT="YourCompanyName YourName (your.email@example.com)"

# Generate a secure secret key (run: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here

# OAuth (if using authentication features)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 3. Run Setup Script

```bash
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

This script will:
- Validate your environment variables
- Create necessary directories
- Pull and build Docker images
- Initialize the database
- Run migrations
- Seed test data

### 4. Start Services

```bash
docker-compose up
```

Or run in detached mode:

```bash
docker-compose up -d
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Alternative Docs**: http://localhost:8000/redoc
- **PostgreSQL**: localhost:5432
- **Elasticsearch**: http://localhost:9200
- **Redis**: localhost:6379

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run locally (outside Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run locally (outside Docker)
npm run dev
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec api alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1
```

### Running Tests

```bash
# Backend tests
docker-compose exec api pytest

# Backend tests with coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Frontend tests
docker-compose exec frontend npm test

# Frontend tests with coverage
docker-compose exec frontend npm test -- --coverage
```

## Useful Scripts

### Reset Database

Drops and recreates the database:

```bash
./scripts/reset-db.sh
```

### Seed Test Data

Populates the database with sample companies and filings:

```bash
./scripts/seed-data.sh
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## API Documentation

### Interactive API Docs

Visit http://localhost:8000/docs for interactive Swagger UI documentation.

### Example API Requests

```bash
# Search filings
curl -X GET "http://localhost:8000/api/v1/filings?form_type=10-K&limit=10"

# Get company info
curl -X GET "http://localhost:8000/api/v1/companies/0000320193"

# Create an alert (requires authentication)
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apple 10-K Filings",
    "conditions": {
      "company_cik": "0000320193",
      "form_types": ["10-K"]
    },
    "notification_method": "email"
  }'
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connection
curl http://localhost:8000/health/db

# Elasticsearch connection
curl http://localhost:8000/health/elasticsearch

# Redis connection
curl http://localhost:8000/health/redis
```

### Service Status

```bash
# Check all services
docker-compose ps

# Check resource usage
docker stats
```

## Troubleshooting

### Elasticsearch fails to start

Increase Docker memory to at least 4GB in Docker Desktop settings.

### Database connection errors

Ensure PostgreSQL is healthy:

```bash
docker-compose ps postgres
docker-compose logs postgres
```

### SEC API rate limiting

The SEC enforces rate limits (10 requests/second). The application includes built-in rate limiting, but if you encounter issues:

1. Verify your `SEC_API_USER_AGENT` is properly formatted
2. Reduce `SEC_API_RATE_LIMIT` in `.env`
3. Check logs: `docker-compose logs worker`

### Port already in use

Change ports in `.env`:

```bash
API_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

## Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Backend**: Follow PEP 8, use `black` for formatting, `flake8` for linting
- **Frontend**: Follow ESLint rules, use Prettier for formatting
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See `/docs` directory for detailed documentation
- **Issues**: https://github.com/yourusername/sec-filings-dashboard/issues
- **Email**: support@yourdomain.com

## Acknowledgments

- SEC EDGAR API for providing access to filing data
- FastAPI framework for the backend
- Next.js framework for the frontend
- Elasticsearch for powerful search capabilities

## Project Status

**Phase**: Foundation & Core Infrastructure (Phase 1)
**Version**: 0.1.0 (Alpha)
**Last Updated**: November 2025

See [IMPLEMENTATION_TASKS.md](./IMPLEMENTATION_TASKS.md) for detailed project roadmap.
