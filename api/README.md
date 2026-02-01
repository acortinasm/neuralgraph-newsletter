# Newsletter API

FastAPI backend service for the NeuralGraph Newsletter system.

## Setup

### Prerequisites

- Python 3.12+
- NeuralGraphDB instance running
- Resend API key (for email delivery)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file or set environment variables:

```env
NEURALGRAPH_URL=http://localhost:3000
RESEND_API_KEY=re_your_api_key
FROM_EMAIL=Newsletter <newsletter@yourdomain.com>
BASE_URL=https://yourdomain.com
SECRET_KEY=your-secure-secret-key
TOKEN_EXPIRE_DAYS=7
```

### Running

**Development:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
api/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Configuration with pydantic-settings
│   ├── database.py      # NeuralGraphDB client
│   ├── models.py        # Pydantic request/response models
│   ├── email.py         # Email sending via Resend
│   └── routers/
│       ├── subscribers.py   # Subscription management
│       ├── newsletters.py   # Newsletter CRUD
│       ├── tracking.py      # Engagement tracking
│       └── analytics.py     # Analytics endpoints
├── Dockerfile
└── requirements.txt
```

## Modules

### `config.py`

Configuration management using `pydantic-settings`. Loads values from environment variables or `.env` file.

### `database.py`

`NeuralGraphClient` class for executing NGQL queries against NeuralGraphDB:
- Async HTTP client using `httpx`
- Parameter interpolation for safe query construction
- Retry logic for transient failures

### `models.py`

Pydantic models for request validation and response serialization:
- `SubscribeRequest` - Email subscription input
- `NewsletterCreate` - Newsletter creation input
- `LinkCreate` - Link addition input
- `TrackOpen`, `TrackClick` - Tracking event inputs

### `email.py`

Email functionality using Resend API:
- Confirmation email sending
- HTML email templating with Jinja2
- Token generation for double opt-in

## Routers

### Subscribers (`/subscribers`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/subscribe` | POST | Create pending subscription |
| `/confirm` | POST | Confirm email with token |
| `/unsubscribe` | POST | Unsubscribe from newsletter |
| `/` | GET | List subscribers |
| `/{email}` | GET | Get subscriber details |

### Newsletters (`/newsletters`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Create newsletter |
| `/` | GET | List newsletters |
| `/{slug}` | GET | Get newsletter with links |
| `/{slug}` | DELETE | Delete draft newsletter |
| `/{slug}/links` | POST | Add link to newsletter |
| `/{slug}/send` | POST | Send to subscribers |

### Tracking (`/track`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/open/{slug}/{email}` | GET | Pixel tracking (returns 1x1 GIF) |
| `/open` | POST | API open tracking |
| `/click` | GET | Redirect click tracking |
| `/click` | POST | API click tracking |
| `/bounce` | POST | Record bounce |
| `/complaint` | POST | Record complaint |

### Analytics (`/analytics`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/subscribers/summary` | GET | Subscriber counts |
| `/subscribers/growth` | GET | Growth over time |
| `/newsletters/performance` | GET | Open/click rates |
| `/engagement/top-subscribers` | GET | Most engaged |
| `/engagement/top-links` | GET | Most clicked links |
| `/topics/engagement` | GET | Topic popularity |
| `/health/bounces` | GET | Bounce rates |
| `/events/recent` | GET | Recent events |

## Docker

### Build

```bash
docker build -t newsletter-api .
```

### Run

```bash
docker run -d \
  --name newsletter-api \
  -p 8000:8000 \
  -e NEURALGRAPH_URL=http://neuralgraph:3000 \
  -e RESEND_API_KEY=your-api-key \
  -e SECRET_KEY=your-secret-key \
  newsletter-api
```

## Development

### API Documentation

When running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

### Adding a New Endpoint

1. Create or edit a router in `app/routers/`
2. Define Pydantic models in `app/models.py`
3. Write NGQL queries using `database.py`
4. Register router in `app/main.py`

### Testing

```bash
pip install pytest pytest-asyncio httpx
pytest
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.0 | Web framework |
| uvicorn | 0.30.0 | ASGI server |
| httpx | 0.27.0 | Async HTTP client |
| pydantic | 2.9.0 | Data validation |
| pydantic-settings | 2.5.0 | Configuration |
| resend | 2.0.0 | Email service |
| jinja2 | 3.1.4 | Email templates |
| email-validator | 2.1.0 | Email validation |
| itsdangerous | 2.2.0 | Token generation |
