"""Tests for input validation and sanitization."""
import pytest
from app.models import (
    SubscribeRequest,
    NewsletterCreate,
    LinkCreate,
    ConfirmRequest,
    sanitize_string,
    validate_slug,
    validate_url,
)


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_escapes_html(self):
        assert sanitize_string("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_limits_length(self):
        long_string = "a" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_handles_none(self):
        assert sanitize_string(None) is None

    def test_handles_empty_string(self):
        assert sanitize_string("") == ""


class TestValidateSlug:
    """Tests for slug validation."""

    def test_valid_slug(self):
        assert validate_slug("issue-1") == "issue-1"
        assert validate_slug("a") == "a"
        assert validate_slug("test123") == "test123"

    def test_invalid_starts_with_hyphen(self):
        with pytest.raises(ValueError):
            validate_slug("-invalid")

    def test_invalid_ends_with_hyphen(self):
        with pytest.raises(ValueError):
            validate_slug("invalid-")

    def test_invalid_uppercase(self):
        with pytest.raises(ValueError):
            validate_slug("INVALID")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError):
            validate_slug("invalid_slug")

    def test_too_long(self):
        with pytest.raises(ValueError):
            validate_slug("a" * 101)


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        assert validate_url("http://example.com") == "http://example.com"

    def test_valid_https_url(self):
        assert validate_url("https://example.com/path?query=1") == "https://example.com/path?query=1"

    def test_invalid_no_protocol(self):
        with pytest.raises(ValueError):
            validate_url("example.com")

    def test_invalid_javascript_url(self):
        with pytest.raises(ValueError):
            validate_url("javascript:alert(1)")

    def test_handles_none(self):
        assert validate_url(None) is None

    def test_too_long(self):
        with pytest.raises(ValueError):
            validate_url("https://example.com/" + "a" * 2000)


class TestSubscribeRequestValidation:
    """Tests for SubscribeRequest model validation."""

    def test_valid_request(self):
        req = SubscribeRequest(email="test@example.com", name="John Doe")
        assert req.email == "test@example.com"
        assert req.name == "John Doe"

    def test_name_sanitized(self):
        req = SubscribeRequest(email="test@example.com", name="  <script>John</script>  ")
        assert req.name == "&lt;script&gt;John&lt;/script&gt;"

    def test_name_too_long(self):
        with pytest.raises(ValueError):
            SubscribeRequest(email="test@example.com", name="a" * 101)

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            SubscribeRequest(email="not-an-email", name="John")


class TestNewsletterCreateValidation:
    """Tests for NewsletterCreate model validation."""

    def test_valid_newsletter(self):
        nl = NewsletterCreate(
            slug="issue-1",
            subject="Test Newsletter",
            preview_text="Preview text here"
        )
        assert nl.slug == "issue-1"

    def test_slug_lowercased(self):
        nl = NewsletterCreate(
            slug="Issue-1",
            subject="Test",
            preview_text="Preview"
        )
        assert nl.slug == "issue-1"

    def test_subject_sanitized(self):
        nl = NewsletterCreate(
            slug="test",
            subject="<b>Bold</b> Newsletter",
            preview_text="Preview"
        )
        assert "&lt;b&gt;" in nl.subject

    def test_invalid_slug_format(self):
        with pytest.raises(ValueError):
            NewsletterCreate(
                slug="invalid slug!",
                subject="Test",
                preview_text="Preview"
            )

    def test_invalid_external_url(self):
        with pytest.raises(ValueError):
            NewsletterCreate(
                slug="test",
                subject="Test",
                preview_text="Preview",
                external_url="not-a-url"
            )


class TestLinkCreateValidation:
    """Tests for LinkCreate model validation."""

    def test_valid_link(self):
        link = LinkCreate(
            url="https://example.com/article",
            title="Great Article",
            topic_slugs=["rust", "performance"]
        )
        assert link.url == "https://example.com/article"

    def test_topic_slugs_validated(self):
        with pytest.raises(ValueError):
            LinkCreate(
                url="https://example.com",
                title="Test",
                topic_slugs=["Invalid Slug!"]
            )

    def test_too_many_topics(self):
        with pytest.raises(ValueError):
            LinkCreate(
                url="https://example.com",
                title="Test",
                topic_slugs=[f"topic-{i}" for i in range(11)]
            )

    def test_invalid_url(self):
        with pytest.raises(ValueError):
            LinkCreate(
                url="not-a-url",
                title="Test"
            )


class TestConfirmRequestValidation:
    """Tests for ConfirmRequest model validation."""

    def test_valid_token(self):
        req = ConfirmRequest(token="abcdefghij1234567890")
        assert req.token == "abcdefghij1234567890"

    def test_token_too_short(self):
        with pytest.raises(ValueError):
            ConfirmRequest(token="short")

    def test_invalid_token_chars(self):
        with pytest.raises(ValueError):
            ConfirmRequest(token="invalid token with spaces!")
