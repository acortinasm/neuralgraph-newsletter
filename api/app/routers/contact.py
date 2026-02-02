from fastapi import APIRouter, HTTPException, Depends, Request

from app.models import ContactRequest, MessageResponse
from app.email import send_contact_email
from app.config import settings
from app.rate_limit import check_rate_limit


router = APIRouter(tags=["contact"])


async def rate_limit_contact(request: Request):
    """Rate limit for contact form submissions."""
    await check_rate_limit(request, max_requests=5, window=60, key_prefix="contact")


@router.post("/contact", response_model=MessageResponse)
async def contact(request: ContactRequest, _: None = Depends(rate_limit_contact)):
    """
    Receive contact form submission and send email notification.

    Rate limited to prevent abuse.
    """
    if not settings.contact_email:
        raise HTTPException(
            status_code=500,
            detail="Contact form is not configured"
        )

    try:
        send_contact_email(
            name=request.name,
            email=request.email,
            message=request.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )

    return MessageResponse(success=True, message="Message sent successfully")
