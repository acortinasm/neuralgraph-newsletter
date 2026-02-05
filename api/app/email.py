import resend
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Set up Jinja2 templates
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def init_resend():
    """Initialize Resend API client."""
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key
        logger.info("Resend API initialized")
    else:
        logger.warning("RESEND_API_KEY not set - emails will NOT be sent")


def render_template(template_name: str, **context) -> str:
    """Render an email template with context."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def send_confirmation_email(to_email: str, name: str, token: str) -> dict:
    """Send subscription confirmation email."""
    confirm_url = f"{settings.base_url}/subscribers/confirm?token={token}"

    html = render_template(
        "confirmation.html",
        name=name,
        confirm_url=confirm_url,
        newsletter_name=settings.api_title,
        expire_days=settings.token_expire_days,
        year=datetime.now().year
    )

    if not settings.resend_api_key:
        logger.warning("Skipping confirmation email (no API key)", to=to_email, confirm_url=confirm_url)
        return {"id": "dev-mode"}

    return resend.Emails.send({
        "from": settings.from_email,
        "to": to_email,
        "subject": f"Confirm your {settings.api_title} subscription",
        "html": html
    })


def send_welcome_email(to_email: str, name: str) -> dict:
    """Send welcome email after confirmation."""
    html = render_template(
        "welcome.html",
        name=name,
        newsletter_name=settings.api_title,
        website_url=settings.base_url,
        year=datetime.now().year
    )

    if not settings.resend_api_key:
        logger.warning("Skipping welcome email (no API key)", to=to_email)
        return {"id": "dev-mode"}

    return resend.Emails.send({
        "from": settings.from_email,
        "to": to_email,
        "subject": f"Welcome to {settings.api_title}!",
        "html": html
    })


def send_newsletter_email(
    to_email: str,
    subject: str,
    content_html: str,
    newsletter_slug: str
) -> dict:
    """Send newsletter to a subscriber."""
    unsubscribe_url = f"{settings.base_url}/unsubscribe?email={to_email}"
    tracking_url = f"{settings.base_url}/track/open/{newsletter_slug}?email={to_email}"

    html = render_template(
        "newsletter.html",
        subject=subject,
        content_html=content_html,
        newsletter_name=settings.api_title,
        unsubscribe_url=unsubscribe_url,
        tracking_url=tracking_url,
        year=datetime.now().year
    )

    if not settings.resend_api_key:
        print(f"[DEV] Newsletter '{newsletter_slug}' to {to_email}")
        return {"id": "dev-mode"}

    return resend.Emails.send({
        "from": settings.from_email,
        "to": to_email,
        "subject": subject,
        "html": html
    })


def send_contact_email(name: str, email: str, message: str) -> dict:
    """Send contact form submission email."""
    html = render_template(
        "contact.html",
        name=name,
        email=email,
        message=message,
        year=datetime.now().year
    )

    if not settings.resend_api_key:
        print(f"[DEV] Contact form from {name} <{email}>: {message[:100]}...")
        return {"id": "dev-mode"}

    return resend.Emails.send({
        "from": settings.from_email,
        "to": settings.contact_email,
        "reply_to": email,
        "subject": f"[Contact] {name}",
        "html": html
    })
