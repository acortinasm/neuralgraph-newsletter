import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import NeuralGraphClient
from app.rate_limit import rate_limiter
from app.auth import create_access_token


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    rate_limiter.requests.clear()
    yield
    rate_limiter.requests.clear()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token for testing."""
    return create_access_token({"sub": "admin", "role": "admin"})


@pytest.fixture
def auth_headers(admin_token):
    """Headers with valid admin authentication."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def mock_db():
    """Mock the database client."""
    with patch("app.routers.subscribers.db") as mock_subscribers_db, \
         patch("app.routers.newsletters.db") as mock_newsletters_db, \
         patch("app.routers.tracking.db") as mock_tracking_db, \
         patch("app.routers.analytics.db") as mock_analytics_db, \
         patch("app.main.db") as mock_main_db:

        mock = AsyncMock(spec=NeuralGraphClient)

        mock_subscribers_db.execute = mock.execute
        mock_newsletters_db.execute = mock.execute
        mock_tracking_db.execute = mock.execute
        mock_analytics_db.execute = mock.execute
        mock_main_db.execute = mock.execute

        yield mock


@pytest.fixture
def mock_email():
    """Mock all email sending functions."""
    with patch("app.routers.subscribers.send_confirmation_email") as mock_confirm, \
         patch("app.routers.subscribers.send_welcome_email") as mock_welcome, \
         patch("app.routers.newsletters.send_newsletter_email") as mock_newsletter:
        yield {
            "confirmation": mock_confirm,
            "welcome": mock_welcome,
            "newsletter": mock_newsletter
        }
