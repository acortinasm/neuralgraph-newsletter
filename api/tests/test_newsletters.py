"""Tests for newsletter endpoints."""


class TestCreateNewsletter:
    """Tests for POST /newsletters/."""

    def test_create_newsletter(self, client, mock_db, auth_headers):
        """Test successful newsletter creation."""
        mock_db.execute.side_effect = [
            [],  # No existing newsletter with slug
            []   # Create result
        ]

        response = client.post(
            "/newsletters/",
            json={
                "slug": "issue-1",
                "subject": "Newsletter Issue #1",
                "preview_text": "This is the first issue",
                "external_url": "https://example.com/issue-1"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_create_duplicate_slug(self, client, mock_db, auth_headers):
        """Test creation fails with duplicate slug."""
        mock_db.execute.return_value = [{"n.slug": "issue-1"}]

        response = client.post(
            "/newsletters/",
            json={
                "slug": "issue-1",
                "subject": "Duplicate",
                "preview_text": "This should fail"
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_newsletter_minimal(self, client, mock_db, auth_headers):
        """Test creation with minimal required fields."""
        mock_db.execute.side_effect = [[], []]

        response = client.post(
            "/newsletters/",
            json={
                "slug": "minimal",
                "subject": "Minimal Newsletter",
                "preview_text": "Just the basics"
            },
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_create_newsletter_requires_auth(self, client):
        """Test that creating newsletter requires authentication."""
        response = client.post(
            "/newsletters/",
            json={
                "slug": "test",
                "subject": "Test",
                "preview_text": "Preview"
            }
        )

        assert response.status_code == 401


class TestAddLink:
    """Tests for POST /newsletters/{slug}/links."""

    def test_add_link_to_newsletter(self, client, mock_db, auth_headers):
        """Test adding a link to a newsletter."""
        mock_db.execute.return_value = []

        response = client.post(
            "/newsletters/issue-1/links",
            json={
                "url": "https://example.com/article",
                "title": "Great Article",
                "description": "An interesting read",
                "topic_slugs": ["rust", "performance"]
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_add_link_without_topics(self, client, mock_db, auth_headers):
        """Test adding a link without topic associations."""
        mock_db.execute.return_value = []

        response = client.post(
            "/newsletters/issue-1/links",
            json={
                "url": "https://example.com/article",
                "title": "Article Without Topics"
            },
            headers=auth_headers
        )

        assert response.status_code == 200


class TestSendNewsletter:
    """Tests for POST /newsletters/{slug}/send."""

    def test_send_newsletter(self, client, mock_db, mock_email, auth_headers):
        """Test successful newsletter send."""
        mock_db.execute.side_effect = [
            [{"n.subject": "Test Newsletter", "n.sent_at": None, "n.content_html": "<p>Content</p>"}],
            [{"s.email": "user1@example.com"}, {"s.email": "user2@example.com"}],  # Active subscribers
            []  # Create delivery records
        ]

        response = client.post("/newsletters/issue-1/send", headers=auth_headers)

        assert response.status_code == 200
        assert "2" in response.json()["message"]

    def test_send_newsletter_sends_emails(self, client, mock_db, mock_email, auth_headers):
        """Test that sending newsletter actually sends emails to subscribers."""
        mock_db.execute.side_effect = [
            [{"n.subject": "Test Newsletter", "n.sent_at": None, "n.content_html": "<p>Hello</p>"}],
            [{"s.email": "user1@example.com"}, {"s.email": "user2@example.com"}],
            []
        ]

        client.post("/newsletters/issue-1/send", headers=auth_headers)

        assert mock_email["newsletter"].call_count == 2
        mock_email["newsletter"].assert_any_call(
            "user1@example.com", "Test Newsletter", "<p>Hello</p>", "issue-1"
        )

    def test_send_newsletter_no_subscribers(self, client, mock_db, mock_email, auth_headers):
        """Test sending newsletter with no active subscribers fails."""
        mock_db.execute.side_effect = [
            [{"n.subject": "Test Newsletter", "n.sent_at": None, "n.content_html": "<p>Content</p>"}],
            []  # No active subscribers
        ]

        response = client.post("/newsletters/issue-1/send", headers=auth_headers)

        assert response.status_code == 400
        assert "no active subscribers" in response.json()["detail"].lower()

    def test_send_nonexistent_newsletter(self, client, mock_db, mock_email, auth_headers):
        """Test sending non-existent newsletter fails."""
        mock_db.execute.return_value = []

        response = client.post("/newsletters/nonexistent/send", headers=auth_headers)

        assert response.status_code == 404

    def test_send_already_sent_newsletter(self, client, mock_db, mock_email, auth_headers):
        """Test re-sending an already sent newsletter fails."""
        mock_db.execute.return_value = [
            {"n.subject": "Test", "n.sent_at": "2024-01-01T00:00:00Z", "n.content_html": "<p>Test</p>"}
        ]

        response = client.post("/newsletters/issue-1/send", headers=auth_headers)

        assert response.status_code == 400
        assert "already sent" in response.json()["detail"].lower()


class TestListNewsletters:
    """Tests for GET /newsletters/."""

    def test_list_all_newsletters(self, client, mock_db, auth_headers):
        """Test listing all newsletters."""
        mock_db.execute.return_value = [
            {
                "n.slug": "issue-1",
                "n.subject": "Issue 1",
                "n.created_at": "2024-01-01T00:00:00Z",
                "n.sent_at": None,
                "n.external_url": None
            },
            {
                "n.slug": "issue-2",
                "n.subject": "Issue 2",
                "n.created_at": "2024-01-02T00:00:00Z",
                "n.sent_at": "2024-01-02T12:00:00Z",
                "n.external_url": "https://example.com/2"
            }
        ]

        response = client.get("/newsletters/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_sent_only(self, client, mock_db, auth_headers):
        """Test listing only sent newsletters."""
        mock_db.execute.return_value = [
            {
                "n.slug": "issue-2",
                "n.subject": "Issue 2",
                "n.sent_at": "2024-01-02T12:00:00Z",
                "n.external_url": "https://example.com/2"
            }
        ]

        response = client.get("/newsletters/?sent_only=true", headers=auth_headers)

        assert response.status_code == 200


class TestGetNewsletter:
    """Tests for GET /newsletters/{slug}."""

    def test_get_newsletter_with_links(self, client, mock_db, auth_headers):
        """Test getting a newsletter with its links."""
        mock_db.execute.return_value = [
            {
                "n.slug": "issue-1",
                "n.subject": "Issue 1",
                "n.preview_text": "Preview",
                "n.sent_at": None,
                "n.external_url": None,
                "links": [
                    {"url": "https://example.com/1", "title": "Article 1"}
                ],
                "topics": ["rust"]
            }
        ]

        response = client.get("/newsletters/issue-1", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["n.slug"] == "issue-1"

    def test_get_nonexistent_newsletter(self, client, mock_db, auth_headers):
        """Test getting a non-existent newsletter."""
        mock_db.execute.return_value = []

        response = client.get("/newsletters/nonexistent", headers=auth_headers)

        assert response.status_code == 404


class TestDeleteNewsletter:
    """Tests for DELETE /newsletters/{slug}."""

    def test_delete_draft_newsletter(self, client, mock_db, auth_headers):
        """Test deleting a draft newsletter."""
        mock_db.execute.return_value = [{"deleted": 1}]

        response = client.delete("/newsletters/draft-issue", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_sent_newsletter_fails(self, client, mock_db, auth_headers):
        """Test deleting a sent newsletter fails."""
        mock_db.execute.return_value = [{"deleted": 0}]

        response = client.delete("/newsletters/sent-issue", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_nonexistent_newsletter(self, client, mock_db, auth_headers):
        """Test deleting a non-existent newsletter."""
        mock_db.execute.return_value = []

        response = client.delete("/newsletters/nonexistent", headers=auth_headers)

        assert response.status_code == 404
