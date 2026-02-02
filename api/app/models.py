import re
import html
from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize string input: escape HTML, limit length, strip whitespace."""
    if not value:
        return value
    # Strip whitespace
    value = value.strip()
    # Limit length
    value = value[:max_length]
    # Escape HTML entities
    value = html.escape(value)
    return value


def validate_slug(value: str) -> str:
    """Validate slug format: lowercase alphanumeric with hyphens."""
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", value):
        raise ValueError("Slug must be lowercase alphanumeric with hyphens, not starting/ending with hyphen")
    if len(value) > 100:
        raise ValueError("Slug must be 100 characters or less")
    return value


def validate_url(value: str) -> str:
    """Validate URL format."""
    if not value:
        return value
    if not re.match(r"^https?://[^\s<>\"']+$", value):
        raise ValueError("Invalid URL format")
    if len(value) > 2000:
        raise ValueError("URL must be 2000 characters or less")
    return value


# ============================================================================
# Subscribers
# ============================================================================

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v, max_length=100)


class ConfirmRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=100)

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        # Token should be alphanumeric with possible URL-safe characters
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid token format")
        return v


class UnsubscribeRequest(BaseModel):
    email: EmailStr


class Subscriber(BaseModel):
    email: str
    name: str
    status: str
    subscribed_at: Optional[str] = None
    confirmed_at: Optional[str] = None


# ============================================================================
# Newsletters
# ============================================================================

class NewsletterCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    preview_text: Optional[str] = Field(None, max_length=500)
    content_md: Optional[str] = Field(None, description="Newsletter content in Markdown")
    external_url: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def validate_newsletter_slug(cls, v: str) -> str:
        return validate_slug(v.lower())

    @field_validator("subject")
    @classmethod
    def sanitize_subject(cls, v: str) -> str:
        return sanitize_string(v, max_length=200)

    @field_validator("preview_text")
    @classmethod
    def sanitize_preview(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_string(v, max_length=500)
        return v

    @field_validator("external_url")
    @classmethod
    def validate_external_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_url(v)
        return v


class NewsletterUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    preview_text: Optional[str] = Field(None, max_length=500)
    content_md: Optional[str] = Field(None, description="Newsletter content in Markdown")
    external_url: Optional[str] = None

    @field_validator("subject")
    @classmethod
    def sanitize_subject(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_string(v, max_length=200)
        return v

    @field_validator("preview_text")
    @classmethod
    def sanitize_preview(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_string(v, max_length=500)
        return v

    @field_validator("external_url")
    @classmethod
    def validate_external_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_url(v)
        return v


class LinkCreate(BaseModel):
    url: str = Field(..., max_length=2000)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    domain: Optional[str] = Field(None, max_length=253)
    topic_slugs: list[str] = []

    @field_validator("url")
    @classmethod
    def validate_link_url(cls, v: str) -> str:
        return validate_url(v)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        return sanitize_string(v, max_length=200)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_string(v, max_length=1000)
        return v

    @field_validator("topic_slugs")
    @classmethod
    def validate_topic_slugs(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("Maximum 10 topics allowed")
        return [validate_slug(slug.lower()) for slug in v]


class NewsletterSend(BaseModel):
    slug: str


# ============================================================================
# Tracking
# ============================================================================

class TrackOpen(BaseModel):
    email: EmailStr
    newsletter_slug: str = Field(..., max_length=100)

    @field_validator("newsletter_slug")
    @classmethod
    def validate_track_slug(cls, v: str) -> str:
        return validate_slug(v.lower())


class TrackClick(BaseModel):
    email: EmailStr
    url: str = Field(..., max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_click_url(cls, v: str) -> str:
        return validate_url(v)


# ============================================================================
# Responses
# ============================================================================

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class SubscriberResponse(BaseModel):
    subscriber: Subscriber
    message: str


class StatsResponse(BaseModel):
    total_subscribers: int
    active: int
    pending: int
    unsubscribed: int


# ============================================================================
# Contact
# ============================================================================

class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=5000)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v, max_length=100)

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        return sanitize_string(v, max_length=5000)
