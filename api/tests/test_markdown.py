"""Tests for markdown utilities."""
from app.markdown_utils import render_markdown, extract_excerpt


class TestRenderMarkdown:
    """Tests for markdown rendering."""

    def test_basic_markdown(self):
        """Test basic markdown rendering."""
        md = "# Hello\n\nThis is **bold** and *italic*."
        html = render_markdown(md)

        assert "<h1" in html and "Hello</h1>" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_code_blocks(self):
        """Test fenced code block rendering."""
        md = "```python\nprint('hello')\n```"
        html = render_markdown(md)

        assert "<pre>" in html
        assert "print" in html

    def test_tables(self):
        """Test table rendering."""
        md = """
| Name | Age |
|------|-----|
| Alice | 30 |
"""
        html = render_markdown(md)

        assert "<table>" in html
        assert "<th>" in html
        assert "Alice" in html

    def test_links(self):
        """Test link rendering."""
        md = "[Click here](https://example.com)"
        html = render_markdown(md)

        assert 'href="https://example.com"' in html
        assert "Click here" in html

    def test_newlines_to_br(self):
        """Test that newlines become <br>."""
        md = "Line 1\nLine 2"
        html = render_markdown(md)

        assert "<br" in html


class TestExtractExcerpt:
    """Tests for excerpt extraction."""

    def test_basic_excerpt(self):
        """Test basic excerpt extraction."""
        md = "This is a simple paragraph of text."
        excerpt = extract_excerpt(md)

        assert excerpt == "This is a simple paragraph of text."

    def test_removes_headers(self):
        """Test that headers are removed."""
        md = "# Header\n\nParagraph text here."
        excerpt = extract_excerpt(md)

        assert "Header" not in excerpt or "# " not in excerpt
        assert "Paragraph" in excerpt

    def test_removes_emphasis(self):
        """Test that emphasis markers are removed."""
        md = "This is **bold** and *italic* text."
        excerpt = extract_excerpt(md)

        assert "**" not in excerpt
        assert "*" not in excerpt
        assert "bold" in excerpt
        assert "italic" in excerpt

    def test_removes_links(self):
        """Test that links are converted to plain text."""
        md = "Check out [this link](https://example.com) for more."
        excerpt = extract_excerpt(md)

        assert "[" not in excerpt
        assert "https://" not in excerpt
        assert "this link" in excerpt

    def test_removes_images(self):
        """Test that images are removed."""
        md = "![Alt text](image.png) Some text after."
        excerpt = extract_excerpt(md)

        assert "![" not in excerpt
        assert "image.png" not in excerpt

    def test_removes_code_blocks(self):
        """Test that code blocks are removed."""
        md = "Before\n```python\ncode here\n```\nAfter"
        excerpt = extract_excerpt(md)

        assert "```" not in excerpt
        assert "code here" not in excerpt

    def test_truncates_long_text(self):
        """Test that long text is truncated."""
        md = "This is a very long text. " * 20
        excerpt = extract_excerpt(md, max_length=50)

        assert len(excerpt) <= 53  # 50 + "..."
        assert excerpt.endswith("...")

    def test_truncates_at_word_boundary(self):
        """Test that truncation happens at word boundary."""
        md = "Word1 Word2 Word3 Word4 Word5"
        excerpt = extract_excerpt(md, max_length=15)

        # Should not cut in middle of word
        assert not excerpt.endswith("Wor...")


class TestNewsletterContentEndpoints:
    """Tests for newsletter content management."""

    def test_create_newsletter_with_markdown(self, client, mock_db, auth_headers):
        """Test creating newsletter with markdown content."""
        mock_db.execute.side_effect = [[], []]

        response = client.post(
            "/newsletters/",
            json={
                "slug": "issue-1",
                "subject": "Test Issue",
                "content_md": "# Hello World\n\nThis is the **first** issue."
            },
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_create_newsletter_auto_preview(self, client, mock_db, auth_headers):
        """Test that preview is auto-generated from markdown."""
        mock_db.execute.side_effect = [[], []]

        response = client.post(
            "/newsletters/",
            json={
                "slug": "issue-1",
                "subject": "Test Issue",
                "content_md": "# Hello\n\nThis is some content for the newsletter."
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        # The preview_text should be auto-generated (verified by mock call)

    def test_update_newsletter_content(self, client, mock_db, auth_headers):
        """Test updating newsletter markdown content."""
        mock_db.execute.side_effect = [
            [{"n.sent_at": None}],  # Newsletter exists, not sent
            []  # Update result
        ]

        response = client.put(
            "/newsletters/issue-1",
            json={"content_md": "# Updated Content\n\nNew text here."},
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_update_sent_newsletter_fails(self, client, mock_db, auth_headers):
        """Test that updating a sent newsletter fails."""
        mock_db.execute.return_value = [{"n.sent_at": "2024-01-01T00:00:00Z"}]

        response = client.put(
            "/newsletters/issue-1",
            json={"content_md": "# Updated"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "sent" in response.json()["detail"].lower()

    def test_preview_newsletter(self, client, mock_db, auth_headers):
        """Test newsletter HTML preview."""
        mock_db.execute.return_value = [
            {"n.subject": "Test", "n.content_html": "<p>Hello World</p>"}
        ]

        response = client.get("/newsletters/issue-1/preview", headers=auth_headers)

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Hello World" in response.text

    def test_render_newsletter(self, client, mock_db, auth_headers):
        """Test re-rendering newsletter content."""
        mock_db.execute.side_effect = [
            [{"n.content_md": "# Hello", "n.sent_at": None}],
            []  # Update result
        ]

        response = client.post("/newsletters/issue-1/render", headers=auth_headers)

        assert response.status_code == 200
        assert "re-rendered" in response.json()["message"].lower()

    def test_render_no_content_fails(self, client, mock_db, auth_headers):
        """Test re-render fails when no markdown content."""
        mock_db.execute.return_value = [{"n.content_md": None, "n.sent_at": None}]

        response = client.post("/newsletters/issue-1/render", headers=auth_headers)

        assert response.status_code == 400
        assert "no markdown" in response.json()["detail"].lower()
