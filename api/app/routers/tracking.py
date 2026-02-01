from fastapi import APIRouter, Response
from app.database import db
from app.models import TrackOpen, TrackClick, MessageResponse

router = APIRouter(prefix="/track", tags=["tracking"])

# 1x1 transparent GIF
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x21, 0xf9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


@router.get("/open/{newsletter_slug}/{email}")
async def track_open_pixel(newsletter_slug: str, email: str):
    """Track email open via tracking pixel."""
    
    try:
        await db.execute(
            """
            MATCH (s:Subscriber {email: $email})-[r:RECEIVED]->(n:Newsletter {slug: $slug})
            SET r.opened_at = COALESCE(r.opened_at, datetime()),
                r.open_count = COALESCE(r.open_count, 0) + 1
            """,
            {"email": email, "slug": newsletter_slug}
        )
    except:
        pass  # Don't fail on tracking errors
    
    return Response(content=TRACKING_PIXEL, media_type="image/gif")


@router.post("/open", response_model=MessageResponse)
async def track_open(data: TrackOpen):
    """Track email open via API call."""
    
    await db.execute(
        """
        MATCH (s:Subscriber {email: $email})-[r:RECEIVED]->(n:Newsletter {slug: $slug})
        SET r.opened_at = COALESCE(r.opened_at, datetime()),
            r.open_count = COALESCE(r.open_count, 0) + 1
        """,
        {"email": data.email, "slug": data.newsletter_slug}
    )
    
    return MessageResponse(message="Open tracked")


@router.get("/click")
async def track_click_redirect(email: str, url: str):
    """Track click and redirect to actual URL."""
    from fastapi.responses import RedirectResponse
    
    try:
        await db.execute(
            """
            MATCH (s:Subscriber {email: $email}), (l:Link {url: $url})
            MERGE (s)-[c:CLICKED]->(l)
            ON CREATE SET c.clicked_at = datetime(), c.click_count = 1
            ON MATCH SET c.click_count = c.click_count + 1
            """,
            {"email": email, "url": url}
        )
    except:
        pass  # Don't fail on tracking errors
    
    return RedirectResponse(url=url)


@router.post("/click", response_model=MessageResponse)
async def track_click(data: TrackClick):
    """Track click via API call."""
    
    await db.execute(
        """
        MATCH (s:Subscriber {email: $email}), (l:Link {url: $url})
        MERGE (s)-[c:CLICKED]->(l)
        ON CREATE SET c.clicked_at = datetime(), c.click_count = 1
        ON MATCH SET c.click_count = c.click_count + 1
        """,
        {"email": data.email, "url": data.url}
    )
    
    return MessageResponse(message="Click tracked")


@router.post("/bounce")
async def track_bounce(email: str, newsletter_slug: str, reason: str = "unknown"):
    """Record a bounce (called from email provider webhook)."""
    
    await db.execute(
        """
        MATCH (s:Subscriber {email: $email})
        SET s.status = "bounced"
        CREATE (e:Event {type: "hard_bounce", occurred_at: datetime(), reason: $reason})
        CREATE (s)-[:LOGGED]->(e)
        WITH s
        MATCH (s)-[r:RECEIVED]->(n:Newsletter {slug: $slug})
        SET r.delivery_status = "bounced"
        """,
        {"email": email, "slug": newsletter_slug, "reason": reason}
    )
    
    return MessageResponse(message="Bounce recorded")


@router.post("/complaint")
async def track_complaint(email: str, feedback_type: str = "spam"):
    """Record a spam complaint (called from email provider webhook)."""
    
    await db.execute(
        """
        MATCH (s:Subscriber {email: $email})
        SET s.status = "complained"
        CREATE (e:Event {type: "complaint", occurred_at: datetime(), reason: $feedback_type})
        CREATE (s)-[:LOGGED]->(e)
        """,
        {"email": email, "feedback_type": feedback_type}
    )
    
    return MessageResponse(message="Complaint recorded")
