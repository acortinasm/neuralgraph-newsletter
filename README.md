# NeuralGraph Newsletter

[![CI](https://github.com/neuralgraph/neuralgraph-newsletter/actions/workflows/ci.yml/badge.svg)](https://github.com/neuralgraph/neuralgraph-newsletter/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A newsletter subscription and engagement tracking system built on [NeuralGraphDB](https://neuralgraph.dev). This platform provides subscriber management, email delivery, engagement tracking (opens, clicks, bounces), comprehensive analytics, and intelligent interest-based personalization using graph-based inference.

## Features

- **Subscriber Management** - Email subscription with double opt-in confirmation, status tracking
- **Newsletter Management** - Create, draft, and send newsletters with categorized links
- **Engagement Tracking** - Track email opens (pixel + API), link clicks, bounces, and complaints
- **Analytics Dashboard** - Subscriber growth, newsletter performance, engagement metrics
- **Interest Inference** - Automatic subscriber interest detection from click behavior
- **Full-Text Search** - Search newsletters, links, subscribers, and topics
- **Graph-Based Personalization** - Leverage relationship patterns for content recommendations
- **Security** - Input sanitization, rate limiting, XSS prevention, JWT/API key auth
- **Markdown Content** - Write newsletters in Markdown, auto-rendered to HTML
- **Production Ready** - Structured logging, health checks, CI/CD, Docker support

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│              (Web App, Email Client, Admin Dashboard)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Newsletter API (FastAPI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Subscribers │  │ Newsletters │  │  Tracking   │  │Analytics│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────────┐  ┌────────┐
       │  Resend  │   │ NeuralGraphDB│  │ Events │
       │  (Email) │   │   (Graph DB) │  │  Log   │
       └──────────┘   └──────────────┘  └────────┘
```

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- NeuralGraphDB instance (running on port 3000)
- Resend API key (for email delivery)

## Quick Start

### 1. Clone and Configure

```bash
cd neuralgraph-newsletter

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### 2. Initialize the Database

```bash
# Run schema initialization
cd init
./init-db.sh
```

This creates:
- Topic nodes (Rust, Graph Databases, AI/ML, Performance, Distributed Systems, Vector Search)
- Full-text search indexes on Newsletter, Link, Subscriber, and Topic entities

### 3. Start the API

**With Docker:**
```bash
docker-compose up -d
```

**Without Docker:**
```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/

# API documentation
open http://localhost:8000/docs
```

## Configuration

Environment variables (set in `.env` or docker-compose):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEURALGRAPH_URL` | NeuralGraphDB connection URL | `http://neuralgraph:3000` |
| `RESEND_API_KEY` | Resend API key for email delivery | - |
| `FROM_EMAIL` | Sender email address | `newsletter@example.com` |
| `BASE_URL` | Public URL for tracking links | `https://neuralgraph.dev` |
| `SECRET_KEY` | Secret for token generation | `change-me-in-production` |
| `TOKEN_EXPIRE_DAYS` | Confirmation token expiry | `7` |

## API Reference

### Subscribers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/subscribers/subscribe` | Subscribe with email (sends confirmation) |
| POST | `/subscribers/confirm` | Confirm email subscription |
| POST | `/subscribers/unsubscribe` | Unsubscribe from newsletter |
| GET | `/subscribers/` | List subscribers (filter by status) |
| GET | `/subscribers/{email}` | Get subscriber details |

**Subscribe Example:**
```bash
curl -X POST http://localhost:8000/subscribers/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "John Doe"}'
```

### Newsletters

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/newsletters/` | Create a new newsletter |
| POST | `/newsletters/{slug}/links` | Add link to newsletter |
| POST | `/newsletters/{slug}/send` | Send newsletter to subscribers |
| GET | `/newsletters/` | List all newsletters |
| GET | `/newsletters/{slug}` | Get newsletter with links |
| DELETE | `/newsletters/{slug}` | Delete unsent draft |

**Create Newsletter Example:**
```bash
curl -X POST http://localhost:8000/newsletters/ \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "issue-42",
    "subject": "NeuralGraph Weekly #42",
    "preview_text": "Graph databases, Rust updates, and more",
    "external_url": "https://neuralgraph.dev/newsletter/42"
  }'
```

### Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/track/open/{newsletter_slug}/{email}` | Pixel-based open tracking (returns 1x1 GIF) |
| POST | `/track/open` | API-based open tracking |
| GET | `/track/click` | Redirect-based click tracking |
| POST | `/track/click` | API-based click tracking |
| POST | `/track/bounce` | Record email bounce |
| POST | `/track/complaint` | Record spam complaint |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/subscribers/summary` | Subscriber counts by status |
| GET | `/analytics/subscribers/growth` | Subscriber growth over time |
| GET | `/analytics/newsletters/performance` | Open/click rates per newsletter |
| GET | `/analytics/engagement/top-subscribers` | Most engaged subscribers |
| GET | `/analytics/engagement/top-links` | Most clicked links |
| GET | `/analytics/topics/engagement` | Topic popularity metrics |
| GET | `/analytics/health/bounces` | Bounce rate analysis |
| GET | `/analytics/events/recent` | Recent events log |

## Data Model

The system uses a graph data model with the following structure:

### Nodes

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Subscriber │     │  Newsletter │     │    Link     │
│─────────────│     │─────────────│     │─────────────│
│ email       │     │ slug        │     │ url         │
│ name        │     │ subject     │     │ title       │
│ status      │     │ preview_text│     │ description │
│ created_at  │     │ sent_at     │     │ domain      │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐
│    Topic    │     │    Event    │
│─────────────│     │─────────────│
│ name        │     │ type        │
│ slug        │     │ details     │
│ description │     │ created_at  │
└─────────────┘     └─────────────┘
```

### Relationships

```
Subscriber -[RECEIVED]-> Newsletter     # Delivery record (opens, clicks)
Subscriber -[CLICKED]-> Link            # Click tracking with counts
Subscriber -[INTERESTED_IN]-> Topic     # Inferred interests with scores
Subscriber -[LOGGED]-> Event            # Audit trail

Newsletter -[LINKS_TO]-> Link           # Newsletter content
Newsletter -[COVERS]-> Topic            # Newsletter categorization

Link -[ABOUT]-> Topic                   # Link categorization
```

### Subscriber Status Flow

```
pending → active → unsubscribed
                 ↘ bounced
                 ↘ complained
```

## Project Structure

```
neuralgraph-newsletter/
├── api/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # NeuralGraphDB client
│   │   ├── models.py            # Pydantic data models
│   │   ├── email.py             # Email sending (Resend)
│   │   └── routers/
│   │       ├── subscribers.py   # Subscription endpoints
│   │       ├── newsletters.py   # Newsletter CRUD
│   │       ├── tracking.py      # Engagement tracking
│   │       └── analytics.py     # Analytics endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── init/                         # Database setup
│   ├── 01-schema.ngql           # Initial topics
│   ├── 02-indexes.ngql          # Search indexes
│   ├── init-db.sh               # Setup script
│   └── queries/                 # Reference NGQL queries
│       ├── subscribers.ngql
│       ├── newsletters.ngql
│       ├── tracking.ngql
│       ├── interests.ngql
│       └── dashboard.ngql
├── docker-compose.yml
└── README.md
```

## Development

### Setup

```bash
cd api
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Running Tests

```bash
cd api
source venv/bin/activate
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest --cov=app            # With coverage
pytest -k "test_subscribe"  # Run specific tests
```

### Linting & Type Checking

```bash
ruff check app/ tests/      # Linting
mypy app/                   # Type checking
```

### API Documentation

FastAPI provides automatic API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Adding New Topics

```ngql
CREATE (t:Topic {
  name: "New Topic",
  slug: "new-topic",
  description: "Description of the new topic"
});
```

### Query Examples

Find subscribers interested in a topic:
```ngql
MATCH (s:Subscriber)-[r:INTERESTED_IN]->(t:Topic {slug: "rust"})
WHERE s.status = "active"
RETURN s.email, s.name, r.score
ORDER BY r.score DESC
LIMIT 100;
```

Get newsletter performance:
```ngql
MATCH (n:Newsletter {slug: "issue-42"})<-[r:RECEIVED]-(s:Subscriber)
RETURN
  COUNT(*) as sent,
  SUM(CASE WHEN r.opened THEN 1 ELSE 0 END) as opens,
  SUM(r.click_count) as total_clicks;
```

## Deployment

### Production Checklist

1. Set a strong `SECRET_KEY` environment variable
2. Configure proper CORS origins in `main.py`
3. Set up HTTPS for tracking endpoints
4. Configure email domain authentication (SPF, DKIM, DMARC)
5. Set up monitoring and alerting
6. Configure rate limiting
7. Enable access logging

### Docker Production

```bash
# Build production image
docker build -t newsletter-api:latest ./api

# Run with production settings
docker run -d \
  --name newsletter-api \
  -p 8000:8000 \
  -e NEURALGRAPH_URL=http://neuralgraph:3000 \
  -e RESEND_API_KEY=your-api-key \
  -e SECRET_KEY=your-secret-key \
  -e FROM_EMAIL="Newsletter <newsletter@yourdomain.com>" \
  -e BASE_URL=https://yourdomain.com \
  newsletter-api:latest
```

## Documentation

- [Integration Guide](docs/INTEGRATION_GUIDE.md) - How to integrate with websites, mobile apps, CI/CD
- [NGQL Queries](docs/QUERIES.md) - Database query reference
- [Changelog](CHANGELOG.md) - Version history
- [API Docs](http://localhost:8000/docs) - Interactive Swagger documentation (when running)

## License

MIT License - See LICENSE file for details.
