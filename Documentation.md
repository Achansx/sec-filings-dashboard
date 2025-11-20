# SEC Filings Dashboard - Technical Documentation

## Overview

The SEC Filings Dashboard is an interactive platform designed for corporate legal teams to efficiently search, analyze, and monitor SEC filings. Built on EdgarTools and the SEC Edgar MCP server, the system provides comprehensive access to all major filing types with advanced search capabilities, real-time alerts, and powerful analytics.

### Core Capabilities

- **Complete Filing Coverage** - Access to all SEC filing types including 10-K/Q, 8-K, S-1, DEF 14A, Forms 3/4/5, and more
- **Advanced Search & Filtering** - Full-text search with filters by company, form type, date range, industry, and keywords
- **Real-time Monitoring** - Customizable alerts for new filings matching your criteria
- **Financial Analytics** - Extract and visualize XBRL financial data across time periods and companies
- **Document Comparison** - Side-by-side redline comparison of filing versions
- **Entity Linking** - Track insider trading activity and cross-reference related filings

## Architecture

### Technology Stack

**Frontend**

- React 18+ with TypeScript
- Material-UI or Ant Design component library
- D3.js / Chart.js for visualizations
- React Router for navigation
- PDF.js for document rendering

**Backend**

- Python 3.11+
- FastAPI web framework
- EdgarTools library for SEC data access
- Celery for background task processing
- Redis for caching

**Data Layer**

- PostgreSQL for structured data (companies, filings metadata, user accounts)
- Elasticsearch for full-text search and analytics
- Redis for session management and caching

**Infrastructure**

- Docker containers for all services
- Kubernetes or Docker Compose for orchestration
- OAuth2/OIDC for enterprise SSO
- HTTPS/TLS encryption for all traffic

### System Architecture Diagram

```
┌─────────────────┐
│  React Frontend │
│   (Port 3000)   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Load    │
    │ Balancer│
    └────┬────┘
         │
    ┌────▼──────────┐
    │  FastAPI      │
    │  API Server   │
    │  (Port 8000)  │
    └───┬───────┬───┘
        │       │
   ┌────▼───┐ ┌▼──────────┐
   │ Postgres│ │Elasticsearch│
   │   DB    │ │   Cluster   │
   └────┬───┘ └─────────────┘
        │
   ┌────▼────────┐
   │   Celery    │
   │   Workers   │
   └─────────────┘
```

## Getting Started

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- 16GB RAM minimum (Elasticsearch requires substantial memory)
- 100GB+ disk space for filing storage and search indices

### Installation

**Clone the Repository**

```bash
git clone https://github.com/your-org/sec-filings-dashboard.git
cd sec-filings-dashboard
```

**Environment Configuration**

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sec_filings
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=sec_filings

# SEC API Configuration
SEC_USER_AGENT="Your Company Name contact@yourcompany.com"
SEC_RATE_LIMIT=10  # requests per second

# Authentication
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# Application
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your_secret_key_here
```

**Launch with Docker Compose**

```bash
docker-compose up -d
```

This starts:

- PostgreSQL on port 5432
- Elasticsearch on port 9200
- Redis on port 6379
- FastAPI backend on port 8000
- React frontend on port 3000
- Celery workers for background tasks

**Initial Data Load**

```bash
# Bootstrap database with company metadata
docker-compose exec api python scripts/bootstrap_companies.py

# Index recent filings (last 90 days)
docker-compose exec api python scripts/initial_index.py --days 90
```

### Development Setup

**Backend Development**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Development**

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the application.

## API Reference

### Authentication

All API endpoints require authentication via OAuth2 bearer token.

```bash
Authorization: Bearer <access_token>
```

### Core Endpoints

#### Search Filings

```http
GET /api/v1/filings/search
```

**Query Parameters**

|Parameter|Type|Description|
|---|---|---|
|`q`|string|Full-text search query|
|`company`|string|Company name or ticker|
|`cik`|string|Central Index Key|
|`form_type`|string|Filing form type (10-K, 8-K, etc.)|
|`date_from`|date|Start date (YYYY-MM-DD)|
|`date_to`|date|End date (YYYY-MM-DD)|
|`sic_code`|string|Standard Industrial Classification code|
|`limit`|integer|Results per page (default: 20, max: 100)|
|`offset`|integer|Pagination offset|

**Response**

```json
{
  "total": 1234,
  "results": [
    {
      "accession_number": "0001193125-24-123456",
      "company_name": "Example Corp",
      "cik": "0001234567",
      "ticker": "EXMP",
      "form_type": "10-K",
      "filing_date": "2024-03-15",
      "accepted_datetime": "2024-03-15T16:30:45",
      "description": "Annual Report",
      "file_url": "/api/v1/filings/0001193125-24-123456"
    }
  ]
}
```

#### Get Filing Details

```http
GET /api/v1/filings/{accession_number}
```

**Response**

```json
{
  "accession_number": "0001193125-24-123456",
  "company": {
    "name": "Example Corp",
    "cik": "0001234567",
    "ticker": "EXMP",
    "sic_code": "7372",
    "industry": "Services-Prepackaged Software"
  },
  "form_type": "10-K",
  "filing_date": "2024-03-15",
  "period_of_report": "2023-12-31",
  "document_count": 87,
  "primary_document": {
    "url": "/api/v1/filings/0001193125-24-123456/document",
    "html_url": "/api/v1/filings/0001193125-24-123456/html",
    "size_bytes": 2456789
  },
  "exhibits": [...]
}
```

#### Get Company Information

```http
GET /api/v1/companies/{cik}
```

**Response**

```json
{
  "cik": "0001234567",
  "name": "Example Corp",
  "ticker": "EXMP",
  "sic_code": "7372",
  "industry_description": "Services-Prepackaged Software",
  "fiscal_year_end": "1231",
  "state_of_incorporation": "DE",
  "recent_filings": [...],
  "filing_counts": {
    "10-K": 10,
    "10-Q": 40,
    "8-K": 125
  }
}
```

#### Get Financial Data

```http
GET /api/v1/companies/{cik}/financials
```

**Query Parameters**

|Parameter|Type|Description|
|---|---|---|
|`form_type`|string|Filing form (10-K or 10-Q)|
|`periods`|integer|Number of periods to retrieve|
|`metrics`|string|Comma-separated list of XBRL concepts|

**Response**

```json
{
  "company": "Example Corp",
  "cik": "0001234567",
  "periods": [
    {
      "filing_date": "2024-03-15",
      "period_end": "2023-12-31",
      "form_type": "10-K",
      "metrics": {
        "Revenues": 1234567890,
        "NetIncomeLoss": 123456789,
        "Assets": 9876543210,
        "Liabilities": 4567891230
      }
    }
  ]
}
```

#### Create Alert

```http
POST /api/v1/alerts
```

**Request Body**

```json
{
  "name": "Tech Company 8-Ks",
  "conditions": {
    "sic_codes": ["7372", "7373"],
    "form_types": ["8-K"],
    "keywords": ["acquisition", "merger"]
  },
  "notification_method": "email",
  "frequency": "immediate"
}
```

#### Compare Filings

```http
POST /api/v1/filings/compare
```

**Request Body**

```json
{
  "accession_number_1": "0001193125-24-123456",
  "accession_number_2": "0001193125-23-654321",
  "comparison_type": "text_diff"
}
```

**Response**

```json
{
  "differences": [
    {
      "section": "Item 1A. Risk Factors",
      "change_type": "addition",
      "text": "New risk factor text...",
      "position": 1234
    }
  ],
  "similarity_score": 0.87
}
```

## Data Pipeline

### Filing Ingestion Process

The system continuously monitors SEC EDGAR for new filings through a multi-stage pipeline:

**1. Discovery**

- Celery task polls SEC submissions API every 5 minutes
- Identifies new filings for monitored companies or matching global criteria
- Filters by form type and other watchlist criteria

**2. Download & Parse**

- Fetches filing via EdgarTools
- Extracts metadata (company info, dates, form type)
- Parses HTML/XML content
- Extracts XBRL financial data if applicable

**3. Storage**

- Inserts metadata record into PostgreSQL
- Caches full document in Redis (TTL: 7 days)
- Stores original filing in object storage (optional)

**4. Indexing**

- Extracts plain text from HTML
- Indexes document in Elasticsearch with metadata
- Updates company filing counts and statistics

**5. Alert Processing**

- Matches new filing against user alert rules
- Queues notifications for matching alerts
- Sends email or in-app notifications

### XBRL Financial Data Extraction

Financial statements from 10-K and 10-Q filings are parsed using EdgarTools XBRL capabilities:

```python
from edgartools import Company

# Get company filings
company = Company("AAPL")
filings = company.get_filings(form="10-K").latest(1)

# Extract financials
financials = filings[0].financials()

# Access specific statements
income_statement = financials.income_statement
balance_sheet = financials.balance_sheet
cash_flow = financials.cash_flow

# Get specific metrics
revenue = income_statement.get_fact("Revenues")
net_income = income_statement.get_fact("NetIncomeLoss")
```

The system standardizes XBRL concepts across companies for comparison:

- Maps vendor-specific tags to standard concepts
- Normalizes values to consistent units (thousands, millions)
- Handles different fiscal year ends
- Tracks restated financials

### Caching Strategy

**Multi-tier caching:**

1. **Browser Cache** - Static assets, filing HTML (24 hours)
2. **Redis Cache** - API responses, search results (1 hour), full documents (7 days)
3. **Database Queries** - Materialized views for expensive aggregations
4. **Elasticsearch** - Document cache with refresh interval (30 seconds)

Cache invalidation triggers:

- New filing ingested for a company
- User updates alert criteria
- Manual cache clear via admin API

## Search Implementation

### Elasticsearch Index Schema

```json
{
  "mappings": {
    "properties": {
      "accession_number": { "type": "keyword" },
      "cik": { "type": "keyword" },
      "company_name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "ticker": { "type": "keyword" },
      "form_type": { "type": "keyword" },
      "filing_date": { "type": "date" },
      "sic_code": { "type": "keyword" },
      "full_text": {
        "type": "text",
        "analyzer": "standard"
      },
      "items": { "type": "keyword" },
      "exhibits": { "type": "keyword" }
    }
  }
}
```

### Search Query Examples

**Basic keyword search with highlighting:**

```json
{
  "query": {
    "multi_match": {
      "query": "cybersecurity breach",
      "fields": ["full_text", "company_name^2"]
    }
  },
  "highlight": {
    "fields": {
      "full_text": {
        "fragment_size": 150,
        "number_of_fragments": 3
      }
    }
  }
}
```

**Filtered search with aggregations:**

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "full_text": "acquisition" } }
      ],
      "filter": [
        { "term": { "form_type": "8-K" } },
        { "range": { "filing_date": { "gte": "2024-01-01" } } }
      ]
    }
  },
  "aggs": {
    "by_company": {
      "terms": { "field": "company_name.keyword", "size": 10 }
    },
    "by_month": {
      "date_histogram": {
        "field": "filing_date",
        "calendar_interval": "month"
      }
    }
  }
}
```

## Security

### Authentication Flow

The application uses OAuth2 with PKCE for authentication:

1. User clicks login, redirected to identity provider
2. After authentication, user redirected back with authorization code
3. Frontend exchanges code for access token and refresh token
4. Access token included in Authorization header for all API requests
5. Refresh token used to obtain new access tokens before expiration

### API Security

**Rate Limiting**

- 100 requests per minute per user for search endpoints
- 1000 requests per minute per user for metadata endpoints
- 10 requests per minute for bulk operations

**Data Access Controls**

- All filings data is public, no row-level restrictions needed
- User preferences, watchlists, and alerts are user-scoped
- Admin endpoints require elevated privileges

**SEC API Compliance**

- User agent header required on all EDGAR requests
- Rate limit: 10 requests per second to SEC
- Automatic retry with exponential backoff on rate limit errors
- Respectful crawling with delays between bulk downloads

### Data Protection

- All passwords hashed with bcrypt (if local auth used)
- Access tokens are JWTs with 1-hour expiration
- Refresh tokens stored in httpOnly cookies
- HTTPS required for all production traffic
- Secrets managed via environment variables or secrets manager
- Audit logging for all data access and modifications

## Deployment

### Docker Compose (Development)

The provided `docker-compose.yml` runs all services locally:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sec_filings
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    depends_on:
      - postgres
      - elasticsearch
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/sec_filings
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/sec_filings
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

volumes:
  postgres_data:
  elasticsearch_data:
```

### Kubernetes (Production)

For production deployment on Kubernetes, separate manifests are provided for each service. Key considerations:

**Scaling Configuration**

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sec-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sec-api
  template:
    spec:
      containers:
      - name: api
        image: your-registry/sec-api:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
          - name: DATABASE_URL
            valueFrom:
              secretKeyRef:
                name: sec-secrets
                key: database-url
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sec-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sec-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Managed Services (AWS Example)**

- RDS PostgreSQL for database (Multi-AZ, automated backups)
- Amazon OpenSearch Service for search cluster
- ElastiCache Redis for caching
- EKS for container orchestration
- S3 for filing document storage
- CloudWatch for logging and monitoring
- Route53 for DNS and load balancing

### CI/CD Pipeline

Automated deployment using GitHub Actions:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker images
        run: |
          docker build -t your-registry/sec-api:${{ github.sha }} ./backend
          docker push your-registry/sec-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/sec-api \
            api=your-registry/sec-api:${{ github.sha }}
          kubectl rollout status deployment/sec-api
```

## Performance Optimization

### Database Optimization

**Indexing Strategy**

```sql
-- Company lookups
CREATE INDEX idx_companies_cik ON companies(cik);
CREATE INDEX idx_companies_ticker ON companies(ticker);

-- Filing searches
CREATE INDEX idx_filings_company_date ON filings(company_cik, filing_date DESC);
CREATE INDEX idx_filings_form_date ON filings(form_type, filing_date DESC);
CREATE INDEX idx_filings_accession ON filings(accession_number);

-- Alert matching
CREATE INDEX idx_filings_sic ON filings(sic_code);
CREATE INDEX idx_filings_items ON filings USING gin(items);
```

**Query Optimization**

- Use prepared statements for repeated queries
- Implement connection pooling (SQLAlchemy with 20-50 connections)
- Partition large tables by year or company
- Use materialized views for complex aggregations

### Elasticsearch Optimization

**Shard Configuration**

```json
{
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.max_result_window": 10000
  }
}
```

**Performance Tips**

- Keep shard size between 10-50GB
- Use bulk indexing for initial data load (batch size: 500-1000 documents)
- Enable index lifecycle management for older data
- Use filters instead of queries when possible (they are cached)

### Frontend Optimization

- Code splitting by route
- Lazy loading of large components (document viewer, charts)
- Virtual scrolling for long search results
- Debounce search input (300ms delay)
- Service worker for offline capabilities
- CDN for static assets

## Monitoring & Observability

### Application Metrics

Track these key metrics:

**API Performance**

- Request rate (requests/second)
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Active connections

**Search Performance**

- Query latency
- Index size and growth rate
- Cache hit ratio
- Search result relevance (click-through rate)

**Data Pipeline**

- Filing ingestion lag (time from SEC publish to indexed)
- Queue depth for background tasks
- Failed ingestion jobs
- Alert processing time

### Logging

Structured logging format (JSON):

```json
{
  "timestamp": "2024-11-20T10:30:45.123Z",
  "level": "INFO",
  "service": "api",
  "endpoint": "/api/v1/filings/search",
  "method": "GET",
  "user_id": "user123",
  "duration_ms": 245,
  "status_code": 200,
  "query_params": {
    "q": "cybersecurity",
    "form_type": "10-K"
  }
}
```

**Log Levels**

- ERROR: Failed operations, exceptions
- WARN: Rate limits hit, slow queries, deprecated API usage
- INFO: Request/response logs, background job completion
- DEBUG: Detailed execution flow (dev only)

### Health Checks

**API Health Endpoint**

```http
GET /health

Response:
{
  "status": "healthy",
  "version": "1.2.3",
  "components": {
    "database": "healthy",
    "elasticsearch": "healthy",
    "redis": "healthy",
    "edgar_api": "healthy"
  },
  "uptime_seconds": 86400
}
```

**Readiness Check**

```http
GET /ready

Response:
{
  "ready": true,
  "checks": {
    "database_migrations": "complete",
    "elasticsearch_indices": "ready",
    "edgar_api_reachable": true
  }
}
```

## Troubleshooting

### Common Issues

**Elasticsearch cluster yellow/red status**

- Check disk space on nodes (requires >15% free)
- Verify all nodes are connected
- Check for unassigned shards: `GET /_cluster/allocation/explain`

**Slow search queries**

- Review query complexity and use of wildcards
- Check cache hit ratio
- Consider adding more replicas for read-heavy workload
- Use `_profile` API to identify bottlenecks

**SEC API rate limiting**

- Verify user agent header is set correctly
- Check rate limit (10 req/sec max)
- Implement exponential backoff in retry logic
- Consider caching more aggressively

**Missing or incomplete filings**

- Check worker logs for ingestion errors
- Verify EDGAR API connectivity
- Review filing date ranges in search
- Check if filing was amended (may have new accession number)

### Debug Mode

Enable verbose logging:

```bash
# Backend
DEBUG=true LOG_LEVEL=DEBUG uvicorn app.main:app

# Frontend
REACT_APP_DEBUG=true npm start
```

### Database Maintenance

```bash
# Vacuum and analyze
docker-compose exec postgres psql -U postgres -d sec_filings -c "VACUUM ANALYZE;"

# Check table sizes
docker-compose exec postgres psql -U postgres -d sec_filings -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Future Enhancements

### Planned Features

- **AI-Powered Analysis** - LLM integration for summarization and Q&A over filings
- **Regulatory Change Tracking** - Automatic detection of disclosure changes
- **Advanced Visualization** - Network graphs for corporate relationships
- **Collaborative Annotations** - Team comments and highlights on filings
- **Export Templates** - Customizable report generation
- **Mobile App** - Native iOS/Android clients
- **Webhook Integration** - Push alerts to Slack, Teams, or custom endpoints

### Technical Improvements

- **GraphQL API** - Alternative to REST for more flexible queries
- **Real-time Updates** - WebSocket connections for live filing notifications
- **Machine Learning** - Classify filing content and predict material events
- **Multi-tenancy** - Support for multiple organizations with data isolation
- **Advanced Caching** - Edge caching with Cloudflare or similar CDN

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

**Python (Backend)**

- Follow PEP 8 guidelines
- Use Black for code formatting
- Type hints required for all functions
- Docstrings for public APIs

**TypeScript (Frontend)**

- Follow Airbnb style guide
- Use Prettier for formatting
- Strict TypeScript mode enabled
- Props interfaces for all components

### Testing

**Backend Tests**

```bash
cd backend
pytest tests/ --cov=app --cov-report=html
```

**Frontend Tests**

```bash
cd frontend
npm test
npm run test:coverage
```

### Pull Request Guidelines

- Include tests for new features
- Update documentation for API changes
- Keep PRs focused on single features/fixes
- Ensure all CI checks pass
- Request review from at least one maintainer

## License

This project is proprietary software developed for [Your Organization]. All rights reserved.

## Support

For technical support or questions:

- Email: support@yourcompany.com
- Slack: #sec-dashboard-support
- Documentation: https://docs.yourcompany.com/sec-dashboard

---

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Maintained by:** Legal Technology Team