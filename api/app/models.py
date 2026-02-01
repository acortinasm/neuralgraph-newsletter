from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ============================================================================
# Subscribers
# ============================================================================

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str


class ConfirmRequest(BaseModel):
    token: str


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
    slug: str
    subject: str
    preview_text: str
    external_url: Optional[str] = None


class LinkCreate(BaseModel):
    url: str
    title: str
    description: Optional[str] = None
    domain: Optional[str] = None
    topic_slugs: list[str] = []


class NewsletterSend(BaseModel):
    slug: str


# ============================================================================
# Tracking
# ============================================================================

class TrackOpen(BaseModel):
    email: str
    newsletter_slug: str


class TrackClick(BaseModel):
    email: str
    url: str


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
