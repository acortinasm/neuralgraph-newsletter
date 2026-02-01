from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime
from app.database import db
from app.email import send_confirmation_email
from app.models import (
    SubscribeRequest,
    ConfirmRequest,
    UnsubscribeRequest,
    MessageResponse,
    Subscriber
)
from app.rate_limit import check_rate_limit
from app.auth import require_admin
import secrets

router = APIRouter(prefix="/subscribers", tags=["subscribers"])


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


async def rate_limit_subscribe(request: Request):
    """Rate limit for subscribe endpoint: 5 requests per minute per IP."""
    await check_rate_limit(request, max_requests=5, window=60, key_prefix="subscribe")


@router.post("/subscribe", response_model=MessageResponse)
async def subscribe(request: SubscribeRequest, _: None = Depends(rate_limit_subscribe)):
    """Subscribe a new user (creates pending subscriber)."""

    existing = await db.execute(
        'MATCH (s:Subscriber) WHERE s.email = $email RETURN s.email, s.status',
        {"email": request.email}
    )
    
    if existing:
        status = existing[0].get("s.status")
        if status == "active":
            raise HTTPException(400, "Email already subscribed")
        elif status == "pending":
            raise HTTPException(400, "Confirmation pending. Check your email.")
    
    token = secrets.token_urlsafe(32)
    
    await db.execute(
        '''
        CREATE (s:Subscriber {
            email: $email,
            name: $name,
            status: "pending",
            subscribed_at: $now,
            confirmation_token: $token
        })
        ''',
        {"email": request.email, "name": request.name, "token": token, "now": now_iso()}
    )
    
    try:
        send_confirmation_email(request.email, request.name, token)
    except Exception:
        # Log error but don't fail the request - subscriber is created
        pass

    return MessageResponse(
        message="Please check your email to confirm subscription.",
        success=True
    )


@router.post("/confirm", response_model=MessageResponse)
async def confirm(request: ConfirmRequest):
    """Confirm subscription with token."""
    
    # Step 1: Find the subscriber with this token
    result = await db.execute(
        '''
        MATCH (s:Subscriber)
        WHERE s.confirmation_token = $token AND s.status = "pending"
        RETURN s.email
        ''',
        {"token": request.token}
    )
    
    if not result:
        raise HTTPException(400, "Invalid or expired token")
    
    email = result[0].get("s.email")
    
    # Step 2: Update the subscriber
    await db.execute(
        '''
        MATCH (s:Subscriber) WHERE s.email = $email
        SET s.status = "active",
            s.confirmed_at = $now,
            s.confirmation_token = null
        ''',
        {"email": email, "now": now_iso()}
    )
    
    return MessageResponse(message="Subscription confirmed!", success=True)


@router.post("/unsubscribe", response_model=MessageResponse)
async def unsubscribe(request: UnsubscribeRequest):
    """Unsubscribe a user."""
    
    result = await db.execute(
        '''
        MATCH (s:Subscriber) WHERE s.email = $email AND s.status = "active"
        RETURN s.email
        ''',
        {"email": request.email}
    )
    
    if not result:
        raise HTTPException(404, "Subscriber not found or already unsubscribed")
    
    await db.execute(
        '''
        MATCH (s:Subscriber) WHERE s.email = $email
        SET s.status = "unsubscribed", s.unsubscribed_at = $now
        ''',
        {"email": request.email, "now": now_iso()}
    )
    
    return MessageResponse(message="Successfully unsubscribed", success=True)


@router.get("/", response_model=list[Subscriber])
async def list_subscribers(status: str = None, limit: int = 100, _: dict = Depends(require_admin)):
    """List subscribers, optionally filtered by status. Requires admin authentication."""
    
    if status:
        rows = await db.execute(
            '''
            MATCH (s:Subscriber) WHERE s.status = $status
            RETURN s.email, s.name, s.status, s.subscribed_at, s.confirmed_at
            LIMIT $limit
            ''',
            {"status": status, "limit": limit}
        )
    else:
        rows = await db.execute(
            '''
            MATCH (s:Subscriber)
            RETURN s.email, s.name, s.status, s.subscribed_at, s.confirmed_at
            LIMIT $limit
            ''',
            {"limit": limit}
        )
    
    return [
        Subscriber(
            email=r["s.email"],
            name=r["s.name"],
            status=r["s.status"],
            subscribed_at=r.get("s.subscribed_at"),
            confirmed_at=r.get("s.confirmed_at")
        )
        for r in rows
    ]


@router.get("/{email}", response_model=Subscriber)
async def get_subscriber(email: str, _: dict = Depends(require_admin)):
    """Get subscriber by email. Requires admin authentication."""
    
    result = await db.execute(
        '''
        MATCH (s:Subscriber) WHERE s.email = $email
        RETURN s.email, s.name, s.status, s.subscribed_at, s.confirmed_at
        ''',
        {"email": email}
    )
    
    if not result:
        raise HTTPException(404, "Subscriber not found")
    
    r = result[0]
    return Subscriber(
        email=r["s.email"],
        name=r["s.name"],
        status=r["s.status"],
        subscribed_at=r.get("s.subscribed_at"),
        confirmed_at=r.get("s.confirmed_at")
    )
