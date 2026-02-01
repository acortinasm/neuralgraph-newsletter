# Changelog

All notable changes to the NeuralGraph Newsletter project are documented here.

## [1.3.0] - 2025-02-01

### Added

#### Email Delivery
- Newsletter sending now actually delivers emails to subscribers via Resend
- Welcome email sent automatically after subscription confirmation
- New `newsletter.html` email template with:
  - Responsive design matching existing templates
  - Open tracking pixel
  - Unsubscribe link
- `send_newsletter_email()` function in `email.py`

### Changed
- `POST /newsletters/{slug}/send` now sends actual emails (previously only created delivery records)
- `POST /subscribers/confirm` now sends welcome email after confirmation
- Subscriber name retrieved during confirmation for personalized welcome

---

## [1.2.0] - 2025-02-01

### Added

#### Authentication
- JWT-based authentication for admin endpoints
- API key authentication (format: `nk_...`)
- New `/auth` endpoints:
  - `POST /auth/login` - Get JWT token
  - `GET /auth/me` - Get current user info
  - `POST /auth/verify` - Verify token validity
  - `POST /auth/api-key` - Generate new API key
- Protected endpoints: newsletters, analytics, subscriber list/get
- Public endpoints: subscribe, confirm, unsubscribe, tracking, health

#### Markdown Content Management
- `content_md` field for newsletter markdown content
- `content_html` field for auto-rendered HTML
- `updated_at` timestamp for newsletters
- New endpoints:
  - `PUT /newsletters/{slug}` - Update draft newsletter
  - `GET /newsletters/{slug}/preview` - HTML preview with styling
  - `POST /newsletters/{slug}/render` - Re-render markdown to HTML
- Auto-generated `preview_text` from markdown content
- Markdown features: headers, code blocks, tables, links, blockquotes

#### New Files
- `api/app/auth.py` - JWT/API key authentication
- `api/app/routers/auth.py` - Auth endpoints
- `api/app/markdown_utils.py` - Markdown rendering utilities
- `api/tests/test_auth.py` - Authentication tests
- `api/tests/test_markdown.py` - Markdown tests

### Changed
- `NewsletterCreate` model now accepts `content_md`
- Added `NewsletterUpdate` model for PATCH updates
- `preview_text` is now optional (auto-generated from markdown)
- All newsletter/analytics/subscriber-list endpoints now require authentication

### Dependencies
- Added `PyJWT==2.9.0` for JWT handling
- Added `Markdown==3.7.0` for content rendering

## [1.1.0] - 2025-02-01

### Added

#### Documentation
- Comprehensive `README.md` with architecture diagram, API reference, and deployment guide
- `api/README.md` with API-specific development documentation
- `docs/QUERIES.md` with complete NGQL query reference
- `CONTRIBUTING.md` with contributor guidelines
- `.env.example` with all configuration options
- `LICENSE` (MIT)

#### Testing
- Complete test suite with 70+ tests
- `test_main.py` - Root and health endpoint tests
- `test_subscribers.py` - Subscriber management tests
- `test_newsletters.py` - Newsletter CRUD tests
- `test_tracking.py` - Engagement tracking tests
- `test_validation.py` - Input validation tests
- `test_rate_limit.py` - Rate limiting tests
- `conftest.py` - Shared fixtures with DB/email mocking
- `pytest.ini` - Test configuration
- `requirements-dev.txt` - Development dependencies (pytest, ruff, mypy)

#### Security
- Input sanitization with HTML escaping (XSS prevention)
- Field length limits on all models
- Slug format validation
- URL format validation (http/https only)
- Token format validation
- Rate limiting on `/subscribers/subscribe` (5 req/min per IP)
- Non-root Docker user

#### Email Templates
- `templates/confirmation.html` - Responsive confirmation email
- `templates/welcome.html` - Welcome email after subscription
- Jinja2 template rendering
- Development mode (logs instead of sending when no API key)

#### Infrastructure
- `.github/workflows/ci.yml` - GitHub Actions CI/CD pipeline
  - Multi-version Python testing (3.11, 3.12)
  - Linting with ruff
  - Type checking with mypy
  - Coverage reporting to Codecov
  - Docker build verification
- Enhanced health checks:
  - `GET /health` - Basic health
  - `GET /health/live` - Liveness probe (K8s)
  - `GET /health/ready` - Readiness probe with DB connectivity check
- Docker improvements:
  - `HEALTHCHECK` instruction
  - Non-root user
  - Health check in docker-compose.yml

#### Logging
- Structured JSON logging for production
- Text logging for development
- Configurable via `LOG_FORMAT` and `LOG_LEVEL`
- Application lifecycle logging

### Changed

- `docker-compose.yml` - Removed hardcoded API key, uses environment variables
- `api/app/config.py` - Added `resend_api_key`, rate limit settings
- `api/app/models.py` - Added Pydantic validators for all inputs
- `api/app/email.py` - Refactored to use Jinja2 templates
- `api/app/main.py` - Added lifespan events, structured logging
- `api/Dockerfile` - Added health check, non-root user, curl

### Security Fixes

- Removed hardcoded Resend API key from docker-compose.yml

## [1.0.0] - 2025-01-01

### Added

- Initial release
- Subscriber management (subscribe, confirm, unsubscribe)
- Newsletter management (create, add links, send)
- Engagement tracking (opens, clicks, bounces, complaints)
- Analytics endpoints
- NeuralGraphDB integration
- Resend email integration
- Docker support
