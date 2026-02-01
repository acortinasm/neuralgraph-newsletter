"""Tests for tracking endpoints."""
import pytest
from unittest.mock import patch


class TestTrackOpen:
    """Tests for open tracking endpoints."""

    def test_pixel_tracking(self, client, mock_db):
        """Test pixel-based open tracking returns GIF."""
        mock_db.execute.return_value = []

        response = client.get("/track/open/issue-1/test@example.com")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"
        # Verify it's a valid GIF (starts with GIF89a)
        assert response.content[:6] == b"GIF89a"

    def test_api_open_tracking(self, client, mock_db):
        """Test API-based open tracking."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/open",
            json={"email": "test@example.com", "newsletter_slug": "issue-1"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Open tracked"


class TestTrackClick:
    """Tests for click tracking endpoints."""

    def test_redirect_click_tracking(self, client, mock_db):
        """Test redirect-based click tracking."""
        mock_db.execute.return_value = []

        response = client.get(
            "/track/click",
            params={
                "email": "test@example.com",
                "url": "https://example.com/article"
            },
            follow_redirects=False
        )

        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com/article"

    def test_api_click_tracking(self, client, mock_db):
        """Test API-based click tracking."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/click",
            json={"email": "test@example.com", "url": "https://example.com/article"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Click tracked"


class TestBounceTracking:
    """Tests for bounce tracking."""

    def test_record_bounce(self, client, mock_db):
        """Test recording a bounce."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/bounce",
            params={
                "email": "bounced@example.com",
                "newsletter_slug": "issue-1",
                "reason": "Mailbox does not exist"
            }
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Bounce recorded"

    def test_record_bounce_default_reason(self, client, mock_db):
        """Test recording a bounce with default reason."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/bounce",
            params={
                "email": "bounced@example.com",
                "newsletter_slug": "issue-1"
            }
        )

        assert response.status_code == 200


class TestComplaintTracking:
    """Tests for complaint tracking."""

    def test_record_complaint(self, client, mock_db):
        """Test recording a spam complaint."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/complaint",
            params={
                "email": "complained@example.com",
                "feedback_type": "spam"
            }
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Complaint recorded"

    def test_record_complaint_default_type(self, client, mock_db):
        """Test recording a complaint with default feedback type."""
        mock_db.execute.return_value = []

        response = client.post(
            "/track/complaint",
            params={"email": "complained@example.com"}
        )

        assert response.status_code == 200
