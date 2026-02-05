from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.database import db
from app.models import NewsletterCreate, NewsletterUpdate, LinkCreate, MessageResponse
from app.auth import require_admin
from app.markdown_utils import render_markdown, extract_excerpt
from app.email import send_newsletter_email

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


def now_iso():
    """Return current UTC time as ISO string (NeuralGraphDB compatible)."""
    return datetime.utcnow().isoformat() + "Z"


def strip_prefix(row: dict) -> dict:
    """Strip node variable prefix (e.g. 'n.slug' -> 'slug') from DB result keys."""
    return {k.split(".", 1)[-1] if "." in k else k: v for k, v in row.items()}


@router.post("/", response_model=MessageResponse)
async def create_newsletter(newsletter: NewsletterCreate, _: dict = Depends(require_admin)):
    """Create a new newsletter draft. Requires admin authentication."""

    # Check if slug exists
    existing = await db.execute(
        "MATCH (n:Newsletter) WHERE n.slug = $slug RETURN n.slug",
        {"slug": newsletter.slug}
    )
    if existing:
        raise HTTPException(400, "Newsletter with this slug already exists")

    # Render markdown to HTML if content provided
    content_html = None
    preview_text = newsletter.preview_text
    if newsletter.content_md:
        content_html = render_markdown(newsletter.content_md)
        # Auto-generate preview if not provided
        if not preview_text:
            preview_text = extract_excerpt(newsletter.content_md)

    await db.execute(
        """
        CREATE (n:Newsletter {
            slug: $slug,
            subject: $subject,
            preview_text: $preview_text,
            content_md: $content_md,
            content_html: $content_html,
            external_url: $external_url,
            created_at: $now,
            updated_at: $now,
            sent_at: null
        })
        """,
        {
            "slug": newsletter.slug,
            "subject": newsletter.subject,
            "preview_text": preview_text,
            "content_md": newsletter.content_md,
            "content_html": content_html,
            "external_url": newsletter.external_url,
            "now": now_iso()
        }
    )

    return MessageResponse(message=f"Newsletter '{newsletter.slug}' created")


@router.put("/{slug}", response_model=MessageResponse)
async def update_newsletter(slug: str, update: NewsletterUpdate, _: dict = Depends(require_admin)):
    """Update a newsletter draft. Requires admin authentication."""

    # Check newsletter exists and not sent
    existing = await db.execute(
        "MATCH (n:Newsletter) WHERE n.slug = $slug RETURN n.sent_at",
        {"slug": slug}
    )
    if not existing:
        raise HTTPException(404, "Newsletter not found")
    if existing[0].get("n.sent_at"):
        raise HTTPException(400, "Cannot update a sent newsletter")

    # Build dynamic update
    updates = ["n.updated_at = $now"]
    params = {"slug": slug, "now": now_iso()}

    if update.subject is not None:
        updates.append("n.subject = $subject")
        params["subject"] = update.subject

    if update.preview_text is not None:
        updates.append("n.preview_text = $preview_text")
        params["preview_text"] = update.preview_text

    if update.external_url is not None:
        updates.append("n.external_url = $external_url")
        params["external_url"] = update.external_url

    if update.content_md is not None:
        updates.append("n.content_md = $content_md")
        updates.append("n.content_html = $content_html")
        params["content_md"] = update.content_md
        params["content_html"] = render_markdown(update.content_md)

        # Auto-update preview if not explicitly set
        if update.preview_text is None:
            updates.append("n.preview_text = $auto_preview")
            params["auto_preview"] = extract_excerpt(update.content_md)

    await db.execute(
        f"""
        MATCH (n:Newsletter) WHERE n.slug = $slug
        SET {", ".join(updates)}
        """,
        params
    )

    return MessageResponse(message=f"Newsletter '{slug}' updated")


@router.post("/{slug}/links", response_model=MessageResponse)
async def add_link(slug: str, link: LinkCreate, _: dict = Depends(require_admin)):
    """Add a link to a newsletter. Requires admin authentication."""

    # Create or update link
    await db.execute(
        """
        MERGE (l:Link {url: $url})
        ON CREATE SET l.title = $title, l.description = $description,
                      l.domain = $domain, l.created_at = $now
        ON MATCH SET l.title = $title, l.description = $description
        """,
        {
            "url": link.url,
            "title": link.title,
            "description": link.description,
            "domain": link.domain,
            "now": now_iso()
        }
    )

    # Associate with topics
    if link.topic_slugs:
        await db.execute(
            """
            MATCH (l:Link) WHERE l.url = $url
            MATCH (t:Topic) WHERE t.slug IN $topic_slugs
            MERGE (l)-[:ABOUT]->(t)
            """,
            {"url": link.url, "topic_slugs": link.topic_slugs}
        )

    # Link to newsletter
    await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        MATCH (l:Link) WHERE l.url = $url
        MERGE (n)-[:LINKS_TO]->(l)
        """,
        {"slug": slug, "url": link.url}
    )

    return MessageResponse(message=f"Link added to newsletter '{slug}'")


@router.post("/{slug}/send", response_model=MessageResponse)
async def send_newsletter(slug: str, _: dict = Depends(require_admin)):
    """Send newsletter to all active subscribers. Requires admin authentication."""

    # Check newsletter exists and not sent
    newsletter = await db.execute(
        "MATCH (n:Newsletter) WHERE n.slug = $slug RETURN n.subject, n.sent_at, n.content_html",
        {"slug": slug}
    )

    if not newsletter:
        raise HTTPException(404, "Newsletter not found")

    if newsletter[0].get("n.sent_at"):
        raise HTTPException(400, "Newsletter already sent")

    subject = newsletter[0].get("n.subject")
    content_html = newsletter[0].get("n.content_html") or ""

    # Get all active subscribers
    subscribers = await db.execute(
        """
        MATCH (s:Subscriber)
        WHERE s.status = "active"
        RETURN s.email
        """
    )

    if not subscribers:
        raise HTTPException(400, "No active subscribers to send to")

    # Send emails and track results
    sent_count = 0
    failed_count = 0

    for sub in subscribers:
        email = sub.get("s.email")
        try:
            send_newsletter_email(email, subject, content_html, slug)
            sent_count += 1
        except Exception:
            failed_count += 1

    # Mark newsletter as sent
    now = now_iso()
    await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        SET n.sent_at = $now
        """,
        {"slug": slug, "now": now}
    )

    if failed_count > 0:
        return MessageResponse(message=f"Newsletter sent to {sent_count} subscribers ({failed_count} failed)")

    return MessageResponse(message=f"Newsletter sent to {sent_count} subscribers")


@router.get("/published")
async def list_published_newsletters():
    """List sent newsletters. Public endpoint for the knowledge page."""
    rows = await db.execute(
        """
        MATCH (n:Newsletter)
        WHERE n.sent_at <> null
        RETURN n.slug, n.subject, n.preview_text, n.sent_at, n.external_url
        ORDER BY n.sent_at DESC
        """
    )
    return [strip_prefix(r) for r in rows]


@router.get("/published/{slug}")
async def get_published_newsletter(slug: str):
    """Get a single sent newsletter by slug. Public endpoint."""
    newsletter = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug AND n.sent_at <> null
        RETURN n.slug, n.subject, n.preview_text, n.content_html, n.sent_at
        """,
        {"slug": slug}
    )
    if not newsletter:
        raise HTTPException(404, "Newsletter not found")
    return strip_prefix(newsletter[0])


@router.get("/")
async def list_newsletters(sent_only: bool = False, _: dict = Depends(require_admin)):
    """List all newsletters. Requires admin authentication."""

    if sent_only:
        query = """
            MATCH (n:Newsletter)
            WHERE n.sent_at <> null
            RETURN n.slug, n.subject, n.preview_text, n.sent_at, n.external_url
            ORDER BY n.sent_at DESC
        """
    else:
        query = """
            MATCH (n:Newsletter)
            RETURN n.slug, n.subject, n.preview_text, n.created_at, n.updated_at, n.sent_at, n.external_url
            ORDER BY n.created_at DESC
        """

    rows = await db.execute(query)
    result = []
    for r in rows:
        item = strip_prefix(r)
        item["status"] = "sent" if item.get("sent_at") else "draft"
        result.append(item)
    return result


@router.get("/{slug}")
async def get_newsletter(slug: str, _: dict = Depends(require_admin)):
    """Get newsletter details with content and links. Requires admin authentication."""

    newsletter = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        RETURN n.slug, n.subject, n.preview_text,
               n.content_md, n.content_html,
               n.created_at, n.updated_at, n.sent_at, n.external_url
        """,
        {"slug": slug}
    )

    if not newsletter:
        raise HTTPException(404, "Newsletter not found")

    result = strip_prefix(newsletter[0])

    # Fetch linked resources separately
    links = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        MATCH (n)-[:LINKS_TO]->(l:Link)
        RETURN l.url, l.title
        """,
        {"slug": slug}
    )
    result["links"] = [{"url": r.get("l.url"), "title": r.get("l.title")} for r in links]

    topics = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        MATCH (n)-[:COVERS]->(t:Topic)
        RETURN t.name
        """,
        {"slug": slug}
    )
    result["topics"] = [r.get("t.name") for r in topics]

    return result


@router.get("/{slug}/preview")
async def preview_newsletter(slug: str, _: dict = Depends(require_admin)):
    """Preview newsletter as rendered HTML. Requires admin authentication."""

    newsletter = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        RETURN n.subject, n.content_html
        """,
        {"slug": slug}
    )

    if not newsletter:
        raise HTTPException(404, "Newsletter not found")

    content_html = newsletter[0].get("n.content_html") or "<p>No content</p>"
    subject = newsletter[0].get("n.subject", "Newsletter Preview")

    # Wrap in basic HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{subject}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                max-width: 700px;
                margin: 40px auto;
                padding: 0 20px;
                color: #333;
            }}
            h1, h2, h3 {{ color: #111; }}
            a {{ color: #10b981; }}
            pre {{
                background: #f4f4f5;
                padding: 16px;
                border-radius: 8px;
                overflow-x: auto;
            }}
            code {{
                background: #f4f4f5;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.9em;
            }}
            pre code {{
                background: none;
                padding: 0;
            }}
            blockquote {{
                border-left: 4px solid #10b981;
                margin: 0;
                padding-left: 16px;
                color: #666;
            }}
            img {{ max-width: 100%; height: auto; }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{ background: #f4f4f5; }}
        </style>
    </head>
    <body>
        <h1>{subject}</h1>
        {content_html}
    </body>
    </html>
    """

    return {"html": html}


@router.post("/{slug}/render", response_model=MessageResponse)
async def render_newsletter_content(slug: str, _: dict = Depends(require_admin)):
    """Re-render markdown to HTML (useful after markdown changes). Requires admin authentication."""

    newsletter = await db.execute(
        "MATCH (n:Newsletter) WHERE n.slug = $slug RETURN n.content_md, n.sent_at",
        {"slug": slug}
    )

    if not newsletter:
        raise HTTPException(404, "Newsletter not found")

    if newsletter[0].get("n.sent_at"):
        raise HTTPException(400, "Cannot re-render a sent newsletter")

    content_md = newsletter[0].get("n.content_md")
    if not content_md:
        raise HTTPException(400, "Newsletter has no markdown content")

    content_html = render_markdown(content_md)

    await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug
        SET n.content_html = $content_html, n.updated_at = $now
        """,
        {"slug": slug, "content_html": content_html, "now": now_iso()}
    )

    return MessageResponse(message=f"Newsletter '{slug}' content re-rendered")


@router.delete("/{slug}", response_model=MessageResponse)
async def delete_newsletter(slug: str, _: dict = Depends(require_admin)):
    """Delete a draft newsletter (not sent). Requires admin authentication."""

    result = await db.execute(
        """
        MATCH (n:Newsletter) WHERE n.slug = $slug AND n.sent_at = null
        DETACH DELETE n
        RETURN COUNT(n) AS deleted
        """,
        {"slug": slug}
    )

    if not result or result[0].get("deleted") == 0:
        raise HTTPException(404, "Newsletter not found or already sent")

    return MessageResponse(message=f"Newsletter '{slug}' deleted")
