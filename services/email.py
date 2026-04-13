import base64
import hashlib
import hmac
import logging

import markdown
import resend

from config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


def _sign_token(payload: str) -> str:
    sig = hmac.new(settings.tracking_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def _verify_token(token: str) -> tuple[str, str] | None:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        payload, sig = decoded.rsplit(":", 1)
        expected = hmac.new(settings.tracking_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return None
        subscriber_id, newsletter_id = payload.split(":")
        return subscriber_id, newsletter_id
    except Exception:
        return None


def make_tracking_token(subscriber_id: str, newsletter_id: str) -> str:
    return _sign_token(f"{subscriber_id}:{newsletter_id}")


def verify_tracking_token(token: str) -> tuple[str, str] | None:
    return _verify_token(token)


def make_tracking_pixel_url(subscriber_id: str, newsletter_id: str) -> str:
    token = make_tracking_token(subscriber_id, newsletter_id)
    return f"{settings.base_url}/track/open?t={token}"


def make_tracking_link(subscriber_id: str, newsletter_id: str, url: str) -> str:
    token = make_tracking_token(subscriber_id, newsletter_id)
    return f"{settings.base_url}/track/click?t={token}&url={url}"


def inject_tracking(html_body: str, subscriber_id: str, newsletter_id: str) -> str:
    pixel_url = make_tracking_pixel_url(subscriber_id, newsletter_id)
    pixel_tag = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
    if "</body>" in html_body:
        return html_body.replace("</body>", f"{pixel_tag}</body>")
    return html_body + pixel_tag


def send_confirmation_email(email: str, name: str, subscriber_id: str, token: str) -> None:
    confirm_url = f"{settings.base_url}/subscribers/{subscriber_id}/confirm/{token}"
    resend.Emails.send(
        {
            "from": settings.from_email,
            "to": [email],
            "subject": "Confirm your subscription to Coral Data",
            "html": (
                f"<p>Hi {name or 'there'},</p>"
                f"<p>Please confirm your subscription by clicking the link below:</p>"
                f'<p><a href="{confirm_url}">Confirm Subscription</a></p>'
                f"<p>If you didn't request this, you can ignore this email.</p>"
            ),
        }
    )


def markdown_to_html(md_body: str) -> str:
    return markdown.markdown(md_body, extensions=["extra", "codehilite", "nl2br"])


def send_newsletter_email(
    email: str,
    name: str,
    subscriber_id: str,
    newsletter_id: str,
    subject: str,
    body: str,
) -> str | None:
    html_body = markdown_to_html(body)
    tracked_html = inject_tracking(html_body, subscriber_id, newsletter_id)
    try:
        result = resend.Emails.send(
            {
                "from": settings.from_email,
                "to": [email],
                "subject": subject,
                "html": tracked_html,
                "text": body,
            }
        )
        return result.get("id") if isinstance(result, dict) else None
    except Exception:
        logger.exception("Failed to send newsletter to %s", email)
        return None
