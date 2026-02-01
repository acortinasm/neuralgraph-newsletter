"""Tests for rate limiting."""
import pytest
import time
from unittest.mock import MagicMock, patch

from app.rate_limit import RateLimiter, get_client_ip


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_allows_requests_under_limit(self):
        limiter = RateLimiter()
        key = "test-key"

        for _ in range(5):
            assert limiter.is_allowed(key, max_requests=5, window=60) is True

    def test_blocks_requests_over_limit(self):
        limiter = RateLimiter()
        key = "test-key"

        # Use up the limit
        for _ in range(5):
            limiter.is_allowed(key, max_requests=5, window=60)

        # Next request should be blocked
        assert limiter.is_allowed(key, max_requests=5, window=60) is False

    def test_resets_after_window(self):
        limiter = RateLimiter()
        key = "test-key"

        # Use up the limit
        for _ in range(5):
            limiter.is_allowed(key, max_requests=5, window=1)

        # Should be blocked
        assert limiter.is_allowed(key, max_requests=5, window=1) is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.is_allowed(key, max_requests=5, window=1) is True

    def test_different_keys_independent(self):
        limiter = RateLimiter()

        # Use up limit for key1
        for _ in range(5):
            limiter.is_allowed("key1", max_requests=5, window=60)

        # key1 should be blocked
        assert limiter.is_allowed("key1", max_requests=5, window=60) is False

        # key2 should still be allowed
        assert limiter.is_allowed("key2", max_requests=5, window=60) is True

    def test_get_retry_after(self):
        limiter = RateLimiter()
        key = "test-key"

        # Make a request
        limiter.is_allowed(key, max_requests=1, window=60)

        retry = limiter.get_retry_after(key, window=60)
        assert 0 < retry <= 60


class TestGetClientIp:
    """Tests for client IP extraction."""

    def test_uses_forwarded_header(self):
        request = MagicMock()
        request.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
        request.client = MagicMock(host="127.0.0.1")

        assert get_client_ip(request) == "1.2.3.4"

    def test_uses_client_host_when_no_forwarded(self):
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock(host="192.168.1.1")

        assert get_client_ip(request) == "192.168.1.1"

    def test_handles_no_client(self):
        request = MagicMock()
        request.headers = {}
        request.client = None

        assert get_client_ip(request) == "unknown"


class TestRateLimitIntegration:
    """Integration tests for rate limiting on endpoints."""

    def test_subscribe_rate_limited(self, client, mock_db, mock_email):
        """Test that subscribe endpoint is rate limited."""
        mock_db.execute.return_value = []

        # Make requests up to the limit
        for i in range(5):
            response = client.post(
                "/subscribers/subscribe",
                json={"email": f"user{i}@example.com", "name": "User"}
            )
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.post(
            "/subscribers/subscribe",
            json={"email": "another@example.com", "name": "User"}
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
