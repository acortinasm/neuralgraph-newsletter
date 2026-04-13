from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from neuralgraph import Session

from auth import require_admin
from database import get_session, driver
from models import (
    NewsletterCreate,
    NewsletterOut,
    NewsletterStats,
    NewsletterUpdate,
    ScheduleRequest,
)
from services import graph
from services.email import send_newsletter_email

router = APIRouter(
    prefix="/newsletters",
    tags=["newsletters"],
    dependencies=[Depends(require_admin)],
)


@router.post("", response_model=NewsletterOut, status_code=201)
def create(body: NewsletterCreate, session: Session = Depends(get_session)):
    nl = graph.create_newsletter(session, body.title, body.subject, body.body)
    if not nl:
        raise HTTPException(status_code=500, detail="Failed to create newsletter")
    return nl


@router.get("", response_model=list[NewsletterOut])
def list_all(session: Session = Depends(get_session)):
    return graph.list_newsletters(session)


@router.get("/{newsletter_id}")
def get_one(newsletter_id: str, session: Session = Depends(get_session)):
    stats = graph.get_newsletter_stats(session, newsletter_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    nl = graph.get_newsletter(session, newsletter_id)
    return {**nl, **stats} if nl else stats


@router.patch("/{newsletter_id}", response_model=NewsletterOut)
def update(newsletter_id: str, body: NewsletterUpdate, session: Session = Depends(get_session)):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    nl = graph.update_newsletter(session, newsletter_id, updates)
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return nl


@router.delete("/{newsletter_id}", status_code=204)
def delete(newsletter_id: str, session: Session = Depends(get_session)):
    deleted = graph.delete_newsletter(session, newsletter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Newsletter not found")


def _send_newsletter_background(newsletter_id: str) -> None:
    with driver.session() as session:
        nl = graph.get_newsletter(session, newsletter_id)
        if not nl:
            return
        subscribers = graph.get_active_subscribers(session)
        graph.set_newsletter_status(session, newsletter_id, "sending")

    for sub in subscribers:
        message_id = send_newsletter_email(
            email=sub["email"],
            name=sub["name"],
            subscriber_id=sub["id"],
            newsletter_id=newsletter_id,
            subject=nl["subject"],
            body=nl["body"],
        )
        if message_id:
            with driver.session() as session:
                graph.record_sent(session, sub["id"], newsletter_id, message_id)

    with driver.session() as session:
        graph.set_newsletter_sent(session, newsletter_id)


@router.post("/{newsletter_id}/send")
def send_newsletter(newsletter_id: str, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    nl = graph.get_newsletter(session, newsletter_id)
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    if nl["status"] == "sent":
        raise HTTPException(status_code=400, detail="Newsletter already sent")
    if nl["status"] == "sending":
        raise HTTPException(status_code=400, detail="Newsletter is currently being sent")
    background_tasks.add_task(_send_newsletter_background, newsletter_id)
    return {"message": "Newsletter send started in background"}


@router.post("/{newsletter_id}/schedule", response_model=NewsletterOut)
def schedule(newsletter_id: str, body: ScheduleRequest, session: Session = Depends(get_session)):
    nl = graph.schedule_newsletter(session, newsletter_id, body.scheduled_at.isoformat())
    if not nl:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return nl
