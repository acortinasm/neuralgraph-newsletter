import logging
import uuid
from datetime import datetime, timezone

from neuralgraph import Session

logger = logging.getLogger(__name__)


def create_subscriber(session: Session, email: str, name: str, confirm_token: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    sub_id = uuid.uuid4().hex

    # Check if subscriber already exists
    existing = session.run(
        "MATCH (s:Subscriber {email: $email}) RETURN s.id AS id",
        parameters={"email": email},
    )
    record = existing.single()

    if record and record["id"] is not None:
        # Update existing subscriber
        session.run(
            """
            MATCH (s:Subscriber {email: $email})
            SET s.confirm_token = $token,
                s.token_expires_at = $expires,
                s.name = CASE WHEN $name <> '' THEN $name ELSE s.name END
            """,
            parameters={
                "email": email,
                "name": name,
                "token": confirm_token,
                "expires": now,
            },
        )
        result = session.run(
            """
            MATCH (s:Subscriber {email: $email})
            RETURN s.id AS id, s.email AS email, s.name AS name, s.status AS status,
                   s.created_at AS created_at
            """,
            parameters={"email": email},
        )
    else:
        # Create new subscriber
        session.run(
            """
            CREATE (s:Subscriber {
                id: $id, email: $email, name: $name, status: 'pending',
                confirm_token: $token, token_expires_at: $expires, created_at: $now
            })
            """,
            parameters={
                "id": sub_id,
                "email": email,
                "name": name,
                "token": confirm_token,
                "expires": now,
                "now": now,
            },
        )
        result = session.run(
            """
            MATCH (s:Subscriber {id: $id})
            RETURN s.id AS id, s.email AS email, s.name AS name, s.status AS status,
                   s.created_at AS created_at
            """,
            parameters={"id": sub_id},
        )

    record = result.single()
    return record.data() if record else {}


def confirm_subscriber(session: Session, subscriber_id: str, token: str) -> dict | None:
    # Check token matches
    check = session.run(
        "MATCH (s:Subscriber {id: $id, confirm_token: $token}) RETURN s.id AS id",
        parameters={"id": subscriber_id, "token": token},
    )
    if not check.single():
        return None

    # Update status
    session.run(
        """
        MATCH (s:Subscriber {id: $id})
        SET s.status = 'active',
            s.confirm_token = NULL,
            s.token_expires_at = NULL,
            s.subscribed_at = $now
        """,
        parameters={
            "id": subscriber_id,
            "now": datetime.now(timezone.utc).isoformat(),
        },
    )

    # Return updated subscriber
    result = session.run(
        """
        MATCH (s:Subscriber {id: $id})
        RETURN s.id AS id, s.email AS email, s.name AS name, s.status AS status
        """,
        parameters={"id": subscriber_id},
    )
    record = result.single()
    return record.data() if record else None


def unsubscribe(session: Session, email: str) -> bool:
    check = session.run(
        "MATCH (s:Subscriber {email: $email}) RETURN s.id AS id",
        parameters={"email": email},
    )
    if not check.single():
        return False
    session.run(
        "MATCH (s:Subscriber {email: $email}) SET s.status = 'unsubscribed'",
        parameters={"email": email},
    )
    return True


def list_subscribers(session: Session, status: str | None = None) -> list[dict]:
    if status:
        result = session.run(
            """
            MATCH (s:Subscriber {status: $status})
            RETURN s.id AS id, s.email AS email, s.name AS name, s.status AS status,
                   s.subscribed_at AS subscribed_at, s.created_at AS created_at
            ORDER BY s.created_at DESC
            """,
            parameters={"status": status},
        )
    else:
        result = session.run(
            """
            MATCH (s:Subscriber)
            RETURN s.id AS id, s.email AS email, s.name AS name, s.status AS status,
                   s.subscribed_at AS subscribed_at, s.created_at AS created_at
            ORDER BY s.created_at DESC
            """
        )
    return [r.data() for r in result]


def get_active_subscribers(session: Session) -> list[dict]:
    result = session.run(
        """
        MATCH (s:Subscriber {status: 'active'})
        RETURN s.id AS id, s.email AS email, s.name AS name
        """
    )
    return [r.data() for r in result]


# --- Newsletters ---

def create_newsletter(session: Session, title: str, subject: str, body: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    nl_id = uuid.uuid4().hex
    session.run(
        """
        CREATE (n:Newsletter {
            id: $id, title: $title, subject: $subject,
            body: $body,
            status: 'draft', created_at: $now, updated_at: $now
        })
        """,
        parameters={
            "id": nl_id,
            "title": title,
            "subject": subject,
            "body": body,
            "now": now,
        },
    )
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               n.body AS body,
               n.status AS status, n.created_at AS created_at, n.updated_at AS updated_at
        """,
        parameters={"id": nl_id},
    )
    record = result.single()
    return record.data() if record else {}


def list_newsletters(session: Session) -> list[dict]:
    result = session.run(
        """
        MATCH (n:Newsletter)
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               n.body AS body,
               n.status AS status, n.scheduled_at AS scheduled_at,
               n.sent_at AS sent_at, n.created_at AS created_at, n.updated_at AS updated_at
        ORDER BY n.created_at DESC
        """
    )
    return [r.data() for r in result]


def get_newsletter(session: Session, newsletter_id: str) -> dict | None:
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               n.body AS body,
               n.status AS status, n.scheduled_at AS scheduled_at,
               n.sent_at AS sent_at, n.created_at AS created_at, n.updated_at AS updated_at
        """,
        parameters={"id": newsletter_id},
    )
    record = result.single()
    return record.data() if record else None


def get_newsletter_stats(session: Session, newsletter_id: str) -> dict | None:
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})
        OPTIONAL MATCH (s1:Subscriber)-[:RECEIVED]->(n)
        OPTIONAL MATCH (s2:Subscriber)-[:OPENED]->(n)
        OPTIONAL MATCH (s3:Subscriber)-[:CLICKED]->(n)
        RETURN n.id AS id, n.title AS title, n.subject AS subject, n.status AS status,
               n.scheduled_at AS scheduled_at, n.sent_at AS sent_at,
               count(DISTINCT s1) AS total_sent,
               count(DISTINCT s2) AS total_opened,
               count(DISTINCT s3) AS total_clicked
        """,
        parameters={"id": newsletter_id},
    )
    record = result.single()
    return record.data() if record else None


def update_newsletter(session: Session, newsletter_id: str, updates: dict) -> dict | None:
    set_clauses = []
    params: dict = {"id": newsletter_id, "now": datetime.now(timezone.utc).isoformat()}
    for key, value in updates.items():
        set_clauses.append(f"n.{key} = ${key}")
        params[key] = value
    set_clauses.append("n.updated_at = $now")

    session.run(
        f"MATCH (n:Newsletter {{id: $id}}) SET {', '.join(set_clauses)}",
        parameters=params,
    )
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               n.body AS body,
               n.status AS status, n.scheduled_at AS scheduled_at,
               n.sent_at AS sent_at, n.created_at AS created_at, n.updated_at AS updated_at
        """,
        parameters={"id": newsletter_id},
    )
    record = result.single()
    return record.data() if record else None


def set_newsletter_status(session: Session, newsletter_id: str, status: str) -> bool:
    check = session.run(
        "MATCH (n:Newsletter {id: $id}) RETURN n.id AS id",
        parameters={"id": newsletter_id},
    )
    if not check.single():
        return False
    session.run(
        "MATCH (n:Newsletter {id: $id}) SET n.status = $status, n.updated_at = $now",
        parameters={
            "id": newsletter_id,
            "status": status,
            "now": datetime.now(timezone.utc).isoformat(),
        },
    )
    return True


def set_newsletter_sent(session: Session, newsletter_id: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    check = session.run(
        "MATCH (n:Newsletter {id: $id}) RETURN n.id AS id",
        parameters={"id": newsletter_id},
    )
    if not check.single():
        return False
    session.run(
        "MATCH (n:Newsletter {id: $id}) SET n.status = 'sent', n.sent_at = $now, n.updated_at = $now",
        parameters={"id": newsletter_id, "now": now},
    )
    return True


def schedule_newsletter(session: Session, newsletter_id: str, scheduled_at: str) -> dict | None:
    check = session.run(
        "MATCH (n:Newsletter {id: $id}) RETURN n.id AS id",
        parameters={"id": newsletter_id},
    )
    if not check.single():
        return None
    session.run(
        "MATCH (n:Newsletter {id: $id}) SET n.status = 'scheduled', n.scheduled_at = $scheduled_at, n.updated_at = $now",
        parameters={
            "id": newsletter_id,
            "scheduled_at": scheduled_at,
            "now": datetime.now(timezone.utc).isoformat(),
        },
    )
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               n.body AS body,
               n.status AS status, n.scheduled_at AS scheduled_at,
               n.sent_at AS sent_at, n.created_at AS created_at, n.updated_at AS updated_at
        """,
        parameters={"id": newsletter_id},
    )
    record = result.single()
    return record.data() if record else None


def delete_newsletter(session: Session, newsletter_id: str) -> bool:
    check = session.run(
        "MATCH (n:Newsletter {id: $id}) RETURN n.id AS id",
        parameters={"id": newsletter_id},
    )
    if not check.single():
        return False
    session.run(
        "MATCH (n:Newsletter {id: $id}) DETACH DELETE n",
        parameters={"id": newsletter_id},
    )
    return True


# --- Tracking ---

def record_sent(session: Session, subscriber_id: str, newsletter_id: str, resend_message_id: str) -> None:
    # Check if relationship exists
    check = session.run(
        "MATCH (s:Subscriber {id: $sid})-[r:RECEIVED]->(n:Newsletter {id: $nid}) RETURN r",
        parameters={"sid": subscriber_id, "nid": newsletter_id},
    )
    if check.single():
        session.run(
            """
            MATCH (s:Subscriber {id: $sid})-[r:RECEIVED]->(n:Newsletter {id: $nid})
            SET r.sent_at = $now, r.resend_message_id = $mid
            """,
            parameters={
                "sid": subscriber_id,
                "nid": newsletter_id,
                "mid": resend_message_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
    else:
        session.run(
            """
            MATCH (s:Subscriber {id: $sid}), (n:Newsletter {id: $nid})
            CREATE (s)-[:RECEIVED {sent_at: $now, resend_message_id: $mid}]->(n)
            """,
            parameters={
                "sid": subscriber_id,
                "nid": newsletter_id,
                "mid": resend_message_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )


def record_open(session: Session, subscriber_id: str, newsletter_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    check = session.run(
        "MATCH (s:Subscriber {id: $sid})-[r:OPENED]->(n:Newsletter {id: $nid}) RETURN r.open_count AS cnt",
        parameters={"sid": subscriber_id, "nid": newsletter_id},
    )
    record = check.single()
    if record:
        session.run(
            """
            MATCH (s:Subscriber {id: $sid})-[r:OPENED]->(n:Newsletter {id: $nid})
            SET r.open_count = r.open_count + 1
            """,
            parameters={"sid": subscriber_id, "nid": newsletter_id},
        )
    else:
        session.run(
            """
            MATCH (s:Subscriber {id: $sid}), (n:Newsletter {id: $nid})
            CREATE (s)-[:OPENED {opened_at: $now, open_count: 1}]->(n)
            """,
            parameters={"sid": subscriber_id, "nid": newsletter_id, "now": now},
        )


def record_click(session: Session, subscriber_id: str, newsletter_id: str, url: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    check = session.run(
        """
        MATCH (s:Subscriber {id: $sid})-[r:CLICKED {url: $url}]->(n:Newsletter {id: $nid})
        RETURN r.click_count AS cnt
        """,
        parameters={"sid": subscriber_id, "nid": newsletter_id, "url": url},
    )
    record = check.single()
    if record:
        session.run(
            """
            MATCH (s:Subscriber {id: $sid})-[r:CLICKED {url: $url}]->(n:Newsletter {id: $nid})
            SET r.click_count = r.click_count + 1
            """,
            parameters={"sid": subscriber_id, "nid": newsletter_id, "url": url},
        )
    else:
        session.run(
            """
            MATCH (s:Subscriber {id: $sid}), (n:Newsletter {id: $nid})
            CREATE (s)-[:CLICKED {url: $url, clicked_at: $now, click_count: 1}]->(n)
            """,
            parameters={"sid": subscriber_id, "nid": newsletter_id, "url": url, "now": now},
        )


# --- Insights ---

def also_read(session: Session, newsletter_id: str, limit: int = 5) -> list[dict]:
    """Readers of newsletter X also opened these other newsletters, ranked by overlap."""
    result = session.run(
        """
        MATCH (n:Newsletter {id: $id})<-[:OPENED]-(s:Subscriber)-[:OPENED]->(other:Newsletter)
        WHERE other.id <> $id
        WITH other, count(DISTINCT s) AS shared_readers
        ORDER BY shared_readers DESC
        LIMIT $limit
        RETURN other.id AS id, other.title AS title, other.subject AS subject,
               shared_readers
        """,
        parameters={"id": newsletter_id, "limit": limit},
    )
    return [r.data() for r in result]


def audience_overlap(session: Session, newsletter_a: str, newsletter_b: str) -> dict:
    """How much audience overlap exists between two newsletters."""
    result = session.run(
        """
        OPTIONAL MATCH (a:Newsletter {id: $a})<-[:OPENED]-(sa:Subscriber)
        WITH collect(DISTINCT sa.id) AS readers_a
        OPTIONAL MATCH (b:Newsletter {id: $b})<-[:OPENED]-(sb:Subscriber)
        WITH readers_a, collect(DISTINCT sb.id) AS readers_b
        WITH readers_a, readers_b,
             [x IN readers_a WHERE x IN readers_b] AS shared
        RETURN size(readers_a) AS readers_a,
               size(readers_b) AS readers_b,
               size(shared) AS shared,
               CASE WHEN size(readers_a) + size(readers_b) - size(shared) > 0
                    THEN toFloat(size(shared)) / (size(readers_a) + size(readers_b) - size(shared))
                    ELSE 0.0 END AS jaccard
        """,
        parameters={"a": newsletter_a, "b": newsletter_b},
    )
    record = result.single()
    return record.data() if record else {}


def subscriber_recommendations(session: Session, subscriber_id: str, limit: int = 5) -> list[dict]:
    """Recommend newsletters the subscriber hasn't read, based on what similar readers opened."""
    result = session.run(
        """
        MATCH (me:Subscriber {id: $id})-[:OPENED]->(n:Newsletter)<-[:OPENED]-(peer:Subscriber)
        WHERE peer.id <> $id
        MATCH (peer)-[:OPENED]->(rec:Newsletter)
        WHERE NOT (me)-[:OPENED]->(rec)
        WITH rec, count(DISTINCT peer) AS score
        ORDER BY score DESC
        LIMIT $limit
        RETURN rec.id AS id, rec.title AS title, rec.subject AS subject, score
        """,
        parameters={"id": subscriber_id, "limit": limit},
    )
    return [r.data() for r in result]


def most_engaged_subscribers(session: Session, limit: int = 10) -> list[dict]:
    """Subscribers ranked by total engagement (opens + clicks)."""
    result = session.run(
        """
        MATCH (s:Subscriber)
        WHERE s.status = 'active'
        OPTIONAL MATCH (s)-[o:OPENED]->(:Newsletter)
        OPTIONAL MATCH (s)-[c:CLICKED]->(:Newsletter)
        WITH s,
             count(DISTINCT o) AS newsletters_opened,
             count(DISTINCT c) AS links_clicked
        WHERE newsletters_opened > 0 OR links_clicked > 0
        RETURN s.id AS id, s.email AS email, s.name AS name,
               newsletters_opened, links_clicked,
               newsletters_opened + links_clicked AS engagement_score
        ORDER BY engagement_score DESC
        LIMIT $limit
        """,
        parameters={"limit": limit},
    )
    return [r.data() for r in result]


def top_newsletters(session: Session, limit: int = 10) -> list[dict]:
    """Newsletters ranked by engagement rates."""
    result = session.run(
        """
        MATCH (n:Newsletter {status: 'sent'})
        OPTIONAL MATCH (:Subscriber)-[r:RECEIVED]->(n)
        OPTIONAL MATCH (:Subscriber)-[o:OPENED]->(n)
        OPTIONAL MATCH (:Subscriber)-[c:CLICKED]->(n)
        WITH n,
             count(DISTINCT r) AS total_sent,
             count(DISTINCT o) AS total_opened,
             count(DISTINCT c) AS total_clicked
        RETURN n.id AS id, n.title AS title, n.subject AS subject,
               total_sent, total_opened, total_clicked,
               CASE WHEN total_sent > 0
                    THEN toFloat(total_opened) / total_sent
                    ELSE 0.0 END AS open_rate,
               CASE WHEN total_opened > 0
                    THEN toFloat(total_clicked) / total_opened
                    ELSE 0.0 END AS click_rate
        ORDER BY open_rate DESC
        LIMIT $limit
        """,
        parameters={"limit": limit},
    )
    return [r.data() for r in result]


def subscriber_journey(session: Session, subscriber_id: str) -> list[dict]:
    """Full engagement timeline for a subscriber."""
    result = session.run(
        """
        MATCH (s:Subscriber {id: $id})-[r]->(n:Newsletter)
        RETURN type(r) AS action, n.id AS newsletter_id, n.title AS title,
               r.sent_at AS sent_at, r.opened_at AS opened_at,
               r.clicked_at AS clicked_at, r.url AS url,
               r.open_count AS open_count, r.click_count AS click_count
        ORDER BY COALESCE(r.sent_at, r.opened_at, r.clicked_at) DESC
        """,
        parameters={"id": subscriber_id},
    )
    return [r.data() for r in result]
