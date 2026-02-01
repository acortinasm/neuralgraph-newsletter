import resend
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from app.config import settings

# Set up Jinja2 templates
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def init_resend():
    """Initialize Resend API client."""
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key


def render_template(template_name: str, **context) -> str:
    """Render an email template with context."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def send_confirmation_email(to_email: str, name: str, token: str) -> dict:
    """Send subscription confirmation email."""
    confirm_url = f"{settings.base_url}/confirm?token={token}"

    html = render_template(
        "confirmation.html",
        name=name,
        confirm_url=confirm_url,
        newsletter_name=settings.api_title,
        expire_days=settings.token_expire_days,
        year=datetime.now().year
    )

    if not settings.resend_api_key:
        # Log instead of sending in development
        print(f"[DEV] Confirmation email to {to_email}: {confirm_url}")
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
        print(f"[DEV] Welcome email to {to_email}")
        return {"id": "dev-mode"}

    return resend.Emails.send({
        "from": settings.from_email,
        "to": to_email,
        "subject": f"Welcome to {settings.api_title}!",
        "html": html
    })
