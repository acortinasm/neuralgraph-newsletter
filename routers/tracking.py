import base64

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, Response
from neuralgraph import Session

from database import get_session
from services.email import verify_tracking_token
from services import graph

router = APIRouter(prefix="/track", tags=["tracking"])

# 1x1 transparent GIF
PIXEL_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


@router.get("/open")
def track_open(t: str = Query(), session: Session = Depends(get_session)):
    ids = verify_tracking_token(t)
    if ids:
        subscriber_id, newsletter_id = ids
        graph.record_open(session, subscriber_id, newsletter_id)
    return Response(content=PIXEL_GIF, media_type="image/gif")


@router.get("/click")
def track_click(t: str = Query(), url: str = Query(), session: Session = Depends(get_session)):
    ids = verify_tracking_token(t)
    if ids:
        subscriber_id, newsletter_id = ids
        graph.record_click(session, subscriber_id, newsletter_id, url)
    return RedirectResponse(url=url)
