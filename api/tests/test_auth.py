"""Tests for authentication."""
import pytest
from unittest.mock import patch
from datetime import timedelta

from app.auth import create_access_token, decode_token, generate_api_key, verify_api_key


class TestJWT:
    """Tests for JWT token handling."""

    def test_create_and_decode_token(self):
        """Test token creation and decoding."""
        token = create_access_token({"sub": "testuser", "role": "admin"})

        payload = decode_token(token)

        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token(self):
        """Test that expired tokens are rejected."""
        from app.auth import AuthError

        token = create_access_token(
            {"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        with pytest.raises(AuthError) as exc:
            decode_token(token)

        assert "expired" in str(exc.value.detail).lower()

    def test_invalid_token(self):
        """Test that invalid tokens are rejected."""
        from app.auth import AuthError

        with pytest.raises(AuthError) as exc:
            decode_token("invalid-token")

        assert "invalid" in str(exc.value.detail).lower()


class TestApiKey:
    """Tests for API key handling."""

    def test_generate_api_key_format(self):
        """Test API key has correct format."""
        key = generate_api_key()

        assert key.startswith("nk_")
        assert len(key) > 20

    def test_verify_api_key(self):
        """Test API key verification."""
        with patch("app.auth.settings") as mock_settings:
            mock_settings.admin_api_key = "nk_test123"

            assert verify_api_key("nk_test123") is True
            assert verify_api_key("nk_wrong") is False


class TestAuthEndpoints:
    """Tests for auth API endpoints."""

    def test_login_success(self, client):
        """Test successful login."""
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "secret123"

            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": "secret123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with wrong credentials."""
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "secret123"

            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": "wrong"}
            )

            assert response.status_code == 401

    def test_login_not_configured(self, client):
        """Test login when password not configured."""
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.admin_password = ""

            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": "any"}
            )

            assert response.status_code == 500
            assert "not configured" in response.json()["detail"].lower()

    def test_get_me_with_jwt(self, client):
        """Test /auth/me with JWT token."""
        token = create_access_token({"sub": "testuser", "role": "admin"})

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["subject"] == "testuser"

    def test_get_me_with_api_key(self, client):
        """Test /auth/me with API key."""
        with patch("app.auth.verify_api_key_from_db") as mock_db_verify, \
             patch("app.auth.settings") as mock_settings:
            mock_db_verify.return_value = None  # No DB key
            mock_settings.admin_api_key = "nk_test123"

            response = client.get(
                "/auth/me",
                headers={"Authorization": "Bearer nk_test123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["type"] == "api_key"

    def test_get_me_unauthenticated(self, client):
        """Test /auth/me without authentication."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_verify_token(self, client):
        """Test token verification endpoint."""
        token = create_access_token({"sub": "testuser", "role": "admin"})

        response = client.post(
            "/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True


class TestProtectedEndpoints:
    """Tests for protected endpoints."""

    def test_newsletters_requires_auth(self, client):
        """Test that newsletter endpoints require authentication."""
        response = client.get("/newsletters/")
        assert response.status_code == 401

        response = client.post("/newsletters/", json={
            "slug": "test",
            "subject": "Test",
            "preview_text": "Preview"
        })
        assert response.status_code == 401

    def test_analytics_requires_auth(self, client):
        """Test that analytics endpoints require authentication."""
        response = client.get("/analytics/subscribers/summary")
        assert response.status_code == 401

    def test_subscriber_list_requires_auth(self, client):
        """Test that subscriber list requires authentication."""
        response = client.get("/subscribers/")
        assert response.status_code == 401

    def test_subscriber_get_requires_auth(self, client):
        """Test that getting a subscriber requires authentication."""
        response = client.get("/subscribers/test@example.com")
        assert response.status_code == 401

    def test_public_endpoints_no_auth(self, client, mock_db, mock_email):
        """Test that public endpoints work without authentication."""
        mock_db.execute.return_value = []

        # Subscribe should work
        response = client.post(
            "/subscribers/subscribe",
            json={"email": "test@example.com", "name": "Test"}
        )
        assert response.status_code == 200

        # Confirm should work (will fail validation, but not auth)
        response = client.post(
            "/subscribers/confirm",
            json={"token": "a" * 32}
        )
        assert response.status_code == 400  # Invalid token, not 401

        # Health endpoints should work
        response = client.get("/health")
        assert response.status_code == 200

    def test_protected_with_valid_token(self, client, mock_db):
        """Test protected endpoints with valid JWT."""
        mock_db.execute.return_value = []
        token = create_access_token({"sub": "admin", "role": "admin"})

        response = client.get(
            "/newsletters/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_protected_with_api_key(self, client, mock_db):
        """Test protected endpoints with API key."""
        mock_db.execute.return_value = []

        with patch("app.auth.verify_api_key_from_db") as mock_db_verify, \
             patch("app.auth.settings") as mock_settings:
            mock_db_verify.return_value = None  # No DB key
            mock_settings.admin_api_key = "nk_validkey123"

            response = client.get(
                "/newsletters/",
                headers={"Authorization": "Bearer nk_validkey123"}
            )

            assert response.status_code == 200
