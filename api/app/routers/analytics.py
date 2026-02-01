from fastapi import APIRouter, Depends
from app.database import db
from app.auth import require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_admin)])


@router.get("/subscribers/summary")
async def subscriber_summary():
    """Get subscriber counts by status."""

    return await db.execute(
        """
        MATCH (s:Subscriber)
        RETURN s.status AS status, COUNT(s) AS count
        ORDER BY count DESC
        """
    )


@router.get("/subscribers/growth")
async def subscriber_growth(months: int = 12):
    """Get subscriber growth over time."""

    return await db.execute(
        """
        MATCH (s:Subscriber)
        WHERE s.confirmed_at IS NOT NULL
        WITH s, substring(toString(s.confirmed_at), 0, 7) AS month
        RETURN month, COUNT(s) AS new_subscribers
        ORDER BY month DESC
        LIMIT $months
        """,
        {"months": months}
    )


@router.get("/newsletters/performance")
async def newsletter_performance(days: int = 90):
    """Get recent newsletter performance metrics."""

    return await db.execute(
        f"""
        MATCH (n:Newsletter)
        WHERE n.sent_at > datetime() - duration("P{days}D")
        OPTIONAL MATCH (s:Subscriber)-[r:RECEIVED]->(n)
        WITH n,
             COUNT(r) AS sent,
             COUNT(CASE WHEN r.opened_at IS NOT NULL THEN 1 END) AS opened,
             COUNT(CASE WHEN r.delivery_status = "bounced" THEN 1 END) AS bounced
        OPTIONAL MATCH (:Subscriber)-[c:CLICKED]->(l:Link)<-[:LINKS_TO]-(n)
        WITH n, sent, opened, bounced, COUNT(c) AS clicks
        RETURN
            n.slug AS slug,
            n.subject AS subject,
            n.sent_at AS sent_at,
            sent,
            opened,
            CASE WHEN sent > 0 THEN round(100.0 * opened / sent, 1) ELSE 0 END AS open_rate,
            clicks,
            CASE WHEN opened > 0 THEN round(100.0 * clicks / opened, 1) ELSE 0 END AS click_rate,
            bounced
        ORDER BY n.sent_at DESC
        """
    )


@router.get("/engagement/top-subscribers")
async def top_subscribers(limit: int = 20):
    """Get most engaged subscribers."""

    return await db.execute(
        """
        MATCH (s:Subscriber)-[r:RECEIVED]->(n:Newsletter)
        WHERE r.opened_at IS NOT NULL AND s.status = "active"
        WITH s, COUNT(r) AS opens
        OPTIONAL MATCH (s)-[c:CLICKED]->(:Link)
        WITH s, opens, COUNT(c) AS clicks
        RETURN s.email AS email, s.name AS name, opens, clicks, opens + clicks AS engagement
        ORDER BY engagement DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )


@router.get("/engagement/top-links")
async def top_links(limit: int = 20):
    """Get most clicked links."""

    return await db.execute(
        """
        MATCH (l:Link)<-[c:CLICKED]-(s:Subscriber)
        OPTIONAL MATCH (l)-[:ABOUT]->(t:Topic)
        RETURN l.title AS title, l.url AS url,
               COUNT(DISTINCT s) AS unique_clickers,
               SUM(c.click_count) AS total_clicks,
               COLLECT(DISTINCT t.name) AS topics
        ORDER BY total_clicks DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )


@router.get("/topics/engagement")
async def topic_engagement():
    """Get engagement by topic."""

    return await db.execute(
        """
        MATCH (t:Topic)<-[:ABOUT]-(l:Link)<-[c:CLICKED]-(s:Subscriber)
        RETURN t.name AS topic, t.slug AS slug,
               COUNT(DISTINCT s) AS unique_clickers,
               SUM(c.click_count) AS total_clicks
        ORDER BY total_clicks DESC
        """
    )


@router.get("/health/bounces")
async def bounce_rate(days: int = 30):
    """Get bounce rate for recent newsletters."""

    return await db.execute(
        f"""
        MATCH (n:Newsletter)
        WHERE n.sent_at > datetime() - duration("P{days}D")
        MATCH (s:Subscriber)-[r:RECEIVED]->(n)
        WITH COUNT(r) AS total_sent,
             COUNT(CASE WHEN r.delivery_status = "bounced" THEN 1 END) AS bounces
        RETURN total_sent, bounces,
               round(100.0 * bounces / total_sent, 2) AS bounce_rate_pct
        """
    )


@router.get("/events/recent")
async def recent_events(days: int = 7, limit: int = 50):
    """Get recent events."""

    return await db.execute(
        f"""
        MATCH (s:Subscriber)-[:LOGGED]->(e:Event)
        WHERE e.occurred_at > datetime() - duration("P{days}D")
        RETURN e.type AS type, s.email AS email, e.occurred_at AS occurred_at, e.reason AS reason
        ORDER BY e.occurred_at DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )
