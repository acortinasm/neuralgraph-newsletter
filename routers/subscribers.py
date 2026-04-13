import secrets

from fastapi import APIRouter, Depends, HTTPException
from neuralgraph import Session

from auth import require_admin
from database import get_session
from models import SubscribeRequest, SubscriberOut, UnsubscribeRequest
from services import graph
from services.email import send_confirmation_email

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


@router.post("", status_code=201)
def subscribe(body: SubscribeRequest, session: Session = Depends(get_session)):
    token = secrets.token_urlsafe(32)
    subscriber = graph.create_subscriber(session, body.email, body.name, token)
    if not subscriber:
        raise HTTPException(status_code=500, detail="Failed to create subscriber")
    send_confirmation_email(body.email, body.name, subscriber["id"], token)
    return {"message": "Confirmation email sent. Please check your inbox."}


@router.get("/{subscriber_id}/confirm/{token}")
def confirm(subscriber_id: str, token: str, session: Session = Depends(get_session)):
    result = graph.confirm_subscriber(session, subscriber_id, token)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid or expired confirmation link")
    return {"message": "Subscription confirmed!", "subscriber": result}


@router.post("/unsubscribe")
def unsubscribe(body: UnsubscribeRequest, session: Session = Depends(get_session)):
    found = graph.unsubscribe(session, body.email)
    if not found:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return {"message": "You have been unsubscribed."}


@router.get("", response_model=list[SubscriberOut], dependencies=[Depends(require_admin)])
def list_subscribers(status: str | None = None, session: Session = Depends(get_session)):
    return graph.list_subscribers(session, status)
