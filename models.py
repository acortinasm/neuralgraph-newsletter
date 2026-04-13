from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Subscribers ---

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str = ""


class UnsubscribeRequest(BaseModel):
    email: EmailStr


class SubscriberOut(BaseModel):
    id: str
    email: str
    name: str
    status: str
    subscribed_at: datetime | None = None
    created_at: datetime | None = None


# --- Newsletters ---

class NewsletterCreate(BaseModel):
    title: str
    subject: str
    body: str  # markdown


class NewsletterUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    body: str | None = None  # markdown


class NewsletterOut(BaseModel):
    id: str
    title: str
    subject: str
    body: str
    status: str
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NewsletterStats(BaseModel):
    id: str
    title: str
    subject: str
    status: str
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None


class ScheduleRequest(BaseModel):
    scheduled_at: datetime
