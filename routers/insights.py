from fastapi import APIRouter, Depends, Query
from neuralgraph import Session

from auth import require_admin
from database import get_session
from services import graph

router = APIRouter(
    prefix="/insights",
    tags=["insights"],
    dependencies=[Depends(require_admin)],
)


@router.get("/newsletters/{newsletter_id}/also-read")
def also_read(newsletter_id: str, limit: int = Query(5, ge=1, le=20), session: Session = Depends(get_session)):
    """Newsletters whose readers also read this one."""
    return graph.also_read(session, newsletter_id, limit)


@router.get("/newsletters/{newsletter_a}/overlap/{newsletter_b}")
def audience_overlap(newsletter_a: str, newsletter_b: str, session: Session = Depends(get_session)):
    """Audience overlap between two newsletters (Jaccard similarity)."""
    return graph.audience_overlap(session, newsletter_a, newsletter_b)


@router.get("/subscribers/{subscriber_id}/recommendations")
def recommendations(subscriber_id: str, limit: int = Query(5, ge=1, le=20), session: Session = Depends(get_session)):
    """Newsletters this subscriber hasn't read, recommended by similar readers."""
    return graph.subscriber_recommendations(session, subscriber_id, limit)


@router.get("/subscribers/{subscriber_id}/journey")
def journey(subscriber_id: str, session: Session = Depends(get_session)):
    """Full engagement timeline for a subscriber."""
    return graph.subscriber_journey(session, subscriber_id)


@router.get("/most-engaged")
def most_engaged(limit: int = Query(10, ge=1, le=50), session: Session = Depends(get_session)):
    """Subscribers ranked by total engagement."""
    return graph.most_engaged_subscribers(session, limit)


@router.get("/top-newsletters")
def top(limit: int = Query(10, ge=1, le=50), session: Session = Depends(get_session)):
    """Sent newsletters ranked by open rate."""
    return graph.top_newsletters(session, limit)
