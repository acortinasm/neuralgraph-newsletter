from fastapi import APIRouter, HTTPException
from app.database import db
from app.models import NewsletterCreate, LinkCreate, NewsletterSend, MessageResponse

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


@router.post("/", response_model=MessageResponse)
async def create_newsletter(newsletter: NewsletterCreate):
    """Create a new newsletter draft."""
    
    # Check if slug exists
    existing = await db.execute(
        "MATCH (n:Newsletter {slug: $slug}) RETURN n.slug",
        {"slug": newsletter.slug}
    )
    if existing:
        raise HTTPException(400, "Newsletter with this slug already exists")
    
    await db.execute(
        """
        CREATE (n:Newsletter {
            slug: $slug,
            subject: $subject,
            preview_text: $preview_text,
            external_url: $external_url,
            created_at: datetime(),
            sent_at: null
        })
        """,
        {
            "slug": newsletter.slug,
            "subject": newsletter.subject,
            "preview_text": newsletter.preview_text,
            "external_url": newsletter.external_url
        }
    )
    
    return MessageResponse(message=f"Newsletter '{newsletter.slug}' created")


@router.post("/{slug}/links", response_model=MessageResponse)
async def add_link(slug: str, link: LinkCreate):
    """Add a link to a newsletter."""
    
    # Create or update link
    await db.execute(
        """
        MERGE (l:Link {url: $url})
        ON CREATE SET l.title = $title, l.description = $description, 
                      l.domain = $domain, l.created_at = datetime()
        ON MATCH SET l.title = $title, l.description = $description
        """,
        {
            "url": link.url,
            "title": link.title,
            "description": link.description,
            "domain": link.domain
        }
    )
    
    # Associate with topics
    if link.topic_slugs:
        await db.execute(
            """
            MATCH (l:Link {url: $url})
            MATCH (t:Topic) WHERE t.slug IN $topic_slugs
            MERGE (l)-[:ABOUT]->(t)
            """,
            {"url": link.url, "topic_slugs": link.topic_slugs}
        )
    
    # Link to newsletter
    await db.execute(
        """
        MATCH (n:Newsletter {slug: $slug})
        MATCH (l:Link {url: $url})
        MERGE (n)-[:LINKS_TO]->(l)
        """,
        {"slug": slug, "url": link.url}
    )
    
    return MessageResponse(message=f"Link added to newsletter '{slug}'")


@router.post("/{slug}/send", response_model=MessageResponse)
async def send_newsletter(slug: str):
    """Send newsletter to all active subscribers."""
    
    # Check newsletter exists and not sent
    newsletter = await db.execute(
        "MATCH (n:Newsletter {slug: $slug}) RETURN n.subject, n.sent_at",
        {"slug": slug}
    )
    
    if not newsletter:
        raise HTTPException(404, "Newsletter not found")
    
    if newsletter[0].get("n.sent_at"):
        raise HTTPException(400, "Newsletter already sent")
    
    # Create delivery records and mark sent
    result = await db.execute(
        """
        MATCH (n:Newsletter {slug: $slug})
        MATCH (s:Subscriber)
        WHERE s.status = "active"
        MERGE (s)-[r:RECEIVED]->(n)
        ON CREATE SET r.sent_at = datetime(), r.delivery_status = "sent"
        WITH n, COUNT(r) AS recipient_count
        SET n.sent_at = datetime()
        RETURN recipient_count
        """,
        {"slug": slug}
    )
    
    count = result[0].get("recipient_count", 0) if result else 0
    
    # TODO: Actually send emails via SMTP/SendGrid
    
    return MessageResponse(message=f"Newsletter sent to {count} subscribers")


@router.get("/")
async def list_newsletters(sent_only: bool = False):
    """List all newsletters."""
    
    if sent_only:
        query = """
            MATCH (n:Newsletter)
            WHERE n.sent_at IS NOT NULL
            RETURN n.slug, n.subject, n.sent_at, n.external_url
            ORDER BY n.sent_at DESC
        """
    else:
        query = """
            MATCH (n:Newsletter)
            RETURN n.slug, n.subject, n.created_at, n.sent_at, n.external_url
            ORDER BY n.created_at DESC
        """
    
    return await db.execute(query)


@router.get("/{slug}")
async def get_newsletter(slug: str):
    """Get newsletter details with links and stats."""
    
    newsletter = await db.execute(
        """
        MATCH (n:Newsletter {slug: $slug})
        OPTIONAL MATCH (n)-[:LINKS_TO]->(l:Link)
        OPTIONAL MATCH (n)-[:COVERS]->(t:Topic)
        RETURN n.slug, n.subject, n.preview_text, n.sent_at, n.external_url,
               COLLECT(DISTINCT {url: l.url, title: l.title}) AS links,
               COLLECT(DISTINCT t.name) AS topics
        """,
        {"slug": slug}
    )
    
    if not newsletter:
        raise HTTPException(404, "Newsletter not found")
    
    return newsletter[0]


@router.delete("/{slug}", response_model=MessageResponse)
async def delete_newsletter(slug: str):
    """Delete a draft newsletter (not sent)."""
    
    result = await db.execute(
        """
        MATCH (n:Newsletter {slug: $slug})
        WHERE n.sent_at IS NULL
        DETACH DELETE n
        RETURN COUNT(n) AS deleted
        """,
        {"slug": slug}
    )
    
    if not result or result[0].get("deleted") == 0:
        raise HTTPException(404, "Newsletter not found or already sent")
    
    return MessageResponse(message=f"Newsletter '{slug}' deleted")
