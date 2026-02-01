"""Tests for subscriber endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


class TestSubscribe:
    """Tests for POST /subscribers/subscribe."""

    def test_subscribe_new_user(self, client, mock_db, mock_email):
        """Test successful subscription for new user."""
        mock_db.execute.return_value = []  # No existing subscriber

        response = client.post(
            "/subscribers/subscribe",
            json={"email": "test@example.com", "name": "Test User"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "check your email" in data["message"].lower()
        mock_email.assert_called_once()

    def test_subscribe_already_active(self, client, mock_db, mock_email):
        """Test subscription fails for already active user."""
        mock_db.execute.return_value = [{"s.email": "test@example.com", "s.status": "active"}]

        response = client.post(
            "/subscribers/subscribe",
            json={"email": "test@example.com", "name": "Test User"}
        )

        assert response.status_code == 400
        assert "already subscribed" in response.json()["detail"].lower()

    def test_subscribe_pending_user(self, client, mock_db, mock_email):
        """Test subscription fails for pending user."""
        mock_db.execute.return_value = [{"s.email": "test@example.com", "s.status": "pending"}]

        response = client.post(
            "/subscribers/subscribe",
            json={"email": "test@example.com", "name": "Test User"}
        )

        assert response.status_code == 400
        assert "pending" in response.json()["detail"].lower()

    def test_subscribe_invalid_email(self, client):
        """Test subscription fails with invalid email."""
        response = client.post(
            "/subscribers/subscribe",
            json={"email": "not-an-email", "name": "Test User"}
        )

        assert response.status_code == 422


class TestConfirm:
    """Tests for POST /subscribers/confirm."""

    def test_confirm_valid_token(self, client, mock_db):
        """Test successful confirmation with valid token."""
        mock_db.execute.side_effect = [
            [{"s.email": "test@example.com"}],  # Find subscriber
            []  # Update result
        ]

        response = client.post(
            "/subscribers/confirm",
            json={"token": "abcdefghij1234567890"}  # 20+ chars required
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_confirm_invalid_token(self, client, mock_db):
        """Test confirmation fails with invalid token."""
        mock_db.execute.return_value = []

        response = client.post(
            "/subscribers/confirm",
            json={"token": "abcdefghij1234567890"}  # Valid format but not in DB
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_confirm_token_too_short(self, client):
        """Test confirmation fails with token that's too short."""
        response = client.post(
            "/subscribers/confirm",
            json={"token": "short"}
        )

        assert response.status_code == 422


class TestUnsubscribe:
    """Tests for POST /subscribers/unsubscribe."""

    def test_unsubscribe_active_user(self, client, mock_db):
        """Test successful unsubscription."""
        mock_db.execute.side_effect = [
            [{"s.email": "test@example.com"}],  # Find active subscriber
            []  # Update result
        ]

        response = client.post(
            "/subscribers/unsubscribe",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_unsubscribe_not_found(self, client, mock_db):
        """Test unsubscription fails for non-existent user."""
        mock_db.execute.return_value = []

        response = client.post(
            "/subscribers/unsubscribe",
            json={"email": "notfound@example.com"}
        )

        assert response.status_code == 404


class TestListSubscribers:
    """Tests for GET /subscribers/."""

    def test_list_all_subscribers(self, client, mock_db, auth_headers):
        """Test listing all subscribers."""
        mock_db.execute.return_value = [
            {
                "s.email": "user1@example.com",
                "s.name": "User 1",
                "s.status": "active",
                "s.subscribed_at": "2024-01-01T00:00:00Z",
                "s.confirmed_at": "2024-01-01T00:01:00Z"
            },
            {
                "s.email": "user2@example.com",
                "s.name": "User 2",
                "s.status": "pending",
                "s.subscribed_at": "2024-01-02T00:00:00Z",
                "s.confirmed_at": None
            }
        ]

        response = client.get("/subscribers/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["email"] == "user1@example.com"

    def test_list_subscribers_by_status(self, client, mock_db, auth_headers):
        """Test filtering subscribers by status."""
        mock_db.execute.return_value = [
            {
                "s.email": "active@example.com",
                "s.name": "Active User",
                "s.status": "active",
                "s.subscribed_at": "2024-01-01T00:00:00Z",
                "s.confirmed_at": "2024-01-01T00:01:00Z"
            }
        ]

        response = client.get("/subscribers/?status=active", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"

    def test_list_subscribers_requires_auth(self, client):
        """Test that listing subscribers requires authentication."""
        response = client.get("/subscribers/")

        assert response.status_code == 401


class TestGetSubscriber:
    """Tests for GET /subscribers/{email}."""

    def test_get_existing_subscriber(self, client, mock_db, auth_headers):
        """Test getting an existing subscriber."""
        mock_db.execute.return_value = [
            {
                "s.email": "test@example.com",
                "s.name": "Test User",
                "s.status": "active",
                "s.subscribed_at": "2024-01-01T00:00:00Z",
                "s.confirmed_at": "2024-01-01T00:01:00Z"
            }
        ]

        response = client.get("/subscribers/test@example.com", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_get_nonexistent_subscriber(self, client, mock_db, auth_headers):
        """Test getting a non-existent subscriber."""
        mock_db.execute.return_value = []

        response = client.get("/subscribers/notfound@example.com", headers=auth_headers)

        assert response.status_code == 404

    def test_get_subscriber_requires_auth(self, client):
        """Test that getting a subscriber requires authentication."""
        response = client.get("/subscribers/test@example.com")

        assert response.status_code == 401
