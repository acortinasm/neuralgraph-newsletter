# NGQL Query Reference

This document provides a reference for the NGQL queries used by the Newsletter API to interact with NeuralGraphDB.

## Table of Contents

- [NeuralGraphDB Compatibility](#neuralgraphdb-compatibility)
- [Subscriber Management](#subscriber-management)
- [Newsletter Management](#newsletter-management)
- [Engagement Tracking](#engagement-tracking)
- [Interest Inference](#interest-inference)
- [Analytics](#analytics)

---

## NeuralGraphDB Compatibility

> **Important:** NeuralGraphDB does not support Neo4j's built-in `datetime()` or `duration()` functions.

The queries in this document show the **logical intent** using Cypher-like syntax. In the actual implementation, all datetime values are computed in Python and passed as query parameters.

### Pattern Used

```python
# Helper function (in each router file)
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

# Query execution
await db.execute(
    "CREATE (n:Node {created_at: $now})",
    {"now": now_iso()}
)
```

### Date Arithmetic

For date calculations (e.g., "7 days from now"), compute in Python:

```python
from datetime import datetime, timedelta

# Instead of: datetime() + duration("P7D")
expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
```

---

## Subscriber Management

### Create Pending Subscriber

Creates a new subscriber in `pending` status with a confirmation token.

```ngql
CREATE (s:Subscriber {
    email: $email,
    name: $name,
    status: "pending",
    subscribed_at: $now,
    confirmation_token: $token
})
RETURN s.email, s.confirmation_token;
```

**Parameters:** `$email`, `$name`, `$token`, `$now` (ISO timestamp from Python)

### Confirm Subscription

Activates a subscriber by validating their confirmation token. After confirmation, a welcome email is sent via Resend.

```ngql
-- Step 1: Find and return subscriber info
MATCH (s:Subscriber)
WHERE s.confirmation_token = $token
  AND s.status = "pending"
RETURN s.email, s.name;

-- Step 2: Update subscriber status
MATCH (s:Subscriber) WHERE s.email = $email
SET s.status = "active",
    s.confirmed_at = $now,
    s.confirmation_token = null
-- Step 3: Welcome email sent via Resend API
```

**Parameters:** `$token`, `$now` (ISO timestamp from Python)

### Unsubscribe

Marks a subscriber as unsubscribed.

```ngql
MATCH (s:Subscriber)
WHERE s.email = $email
SET s.status = "unsubscribed", s.unsubscribed_at = $now;
```

**Parameters:** `$email`, `$now` (ISO timestamp from Python)

### Get Subscriber with Interests

Retrieves subscriber details along with their inferred topic interests.

```ngql
MATCH (s:Subscriber {email: $email})
OPTIONAL MATCH (s)-[i:INTERESTED_IN]->(t:Topic)
RETURN s, COLLECT({topic: t.name, score: i.score}) AS interests
ORDER BY i.score DESC;
```

**Parameters:** `$email`

### List Active Subscribers

```ngql
MATCH (s:Subscriber)
WHERE s.status = "active"
RETURN s.email, s.name, s.confirmed_at
ORDER BY s.confirmed_at DESC;
```

### Subscriber Counts by Status

```ngql
MATCH (s:Subscriber)
RETURN s.status AS status, COUNT(s) AS count
ORDER BY count DESC;
```

---

## Newsletter Management

### Create Newsletter

```ngql
CREATE (n:Newsletter {
    slug: $slug,
    subject: $subject,
    preview_text: $preview_text,
    external_url: $external_url,
    created_at: $now,
    sent_at: null
})
RETURN n;
```

**Parameters:** `$slug`, `$subject`, `$preview_text`, `$external_url`, `$now` (ISO timestamp from Python)

### Create or Update Link

Uses MERGE to create a link if it doesn't exist, or update if it does.

```ngql
MERGE (l:Link {url: $url})
ON CREATE SET
    l.title = $title,
    l.description = $description,
    l.domain = $domain,
    l.created_at = $now
ON MATCH SET
    l.title = $title,
    l.description = $description
RETURN l;
```

**Parameters:** `$url`, `$title`, `$description`, `$domain`, `$now` (ISO timestamp from Python)

### Associate Link with Topics

```ngql
MATCH (l:Link {url: $url})
MATCH (t:Topic) WHERE t.slug IN $topic_slugs
MERGE (l)-[:ABOUT]->(t)
RETURN l, COLLECT(t.name) AS topics;
```

**Parameters:** `$url`, `$topic_slugs` (array)

### Add Link to Newsletter

```ngql
MATCH (n:Newsletter {slug: $newsletter_slug})
MATCH (l:Link {url: $url})
MERGE (n)-[r:LINKS_TO]->(l)
SET r.position = $position
RETURN n.subject, l.title, r.position;
```

**Parameters:** `$newsletter_slug`, `$url`, `$position`

### Send Newsletter

Sends emails to all active subscribers via Resend, then creates delivery records in the database.

**Flow:**
1. Fetch newsletter content (subject, HTML)
2. Query all active subscribers
3. Send email to each subscriber via Resend API
4. Create `RECEIVED` relationships and mark newsletter as sent

```ngql
-- Step 1: Get active subscribers
MATCH (s:Subscriber)
WHERE s.status = "active"
RETURN s.email;

-- Step 2: After sending emails, create delivery records
MATCH (n:Newsletter {slug: $newsletter_slug})
MATCH (s:Subscriber)
WHERE s.status = "active"
MERGE (s)-[r:RECEIVED]->(n)
ON CREATE SET r.sent_at = $now, r.delivery_status = "sent"
WITH n
SET n.sent_at = $now;
```

**Parameters:** `$newsletter_slug`, `$now` (ISO timestamp from Python)

### Get Newsletter with Links and Topics

```ngql
MATCH (n:Newsletter {slug: $slug})
OPTIONAL MATCH (n)-[:LINKS_TO]->(l:Link)
OPTIONAL MATCH (n)-[:COVERS]->(t:Topic)
RETURN n,
       COLLECT(DISTINCT {url: l.url, title: l.title}) AS links,
       COLLECT(DISTINCT t.name) AS topics;
```

**Parameters:** `$slug`

### List Sent Newsletters

```ngql
MATCH (n:Newsletter)
WHERE n.sent_at IS NOT NULL
RETURN n.slug, n.subject, n.sent_at, n.external_url
ORDER BY n.sent_at DESC;
```

### Delete Draft Newsletter

Only deletes newsletters that haven't been sent yet.

```ngql
MATCH (n:Newsletter {slug: $slug})
WHERE n.sent_at IS NULL
DETACH DELETE n;
```

**Parameters:** `$slug`

---

## Engagement Tracking

### Record Email Open

```ngql
MATCH (s:Subscriber {email: $email})-[r:RECEIVED]->(n:Newsletter {slug: $slug})
SET r.opened_at = COALESCE(r.opened_at, $now),
    r.open_count = COALESCE(r.open_count, 0) + 1
RETURN s.email, n.slug, r.open_count;
```

**Parameters:** `$email`, `$slug`, `$now` (ISO timestamp from Python)

### Record Link Click

```ngql
MATCH (s:Subscriber {email: $email})
MATCH (l:Link {url: $url})
MERGE (s)-[c:CLICKED]->(l)
ON CREATE SET c.clicked_at = $now, c.click_count = 1
ON MATCH SET c.click_count = c.click_count + 1
RETURN s.email, l.url, c.click_count;
```

**Parameters:** `$email`, `$url`, `$now` (ISO timestamp from Python)

### Record Bounce

```ngql
MATCH (s:Subscriber {email: $email})
SET s.status = CASE
    WHEN $bounce_type = "hard" THEN "bounced"
    ELSE s.status
END
CREATE (e:Event {
    type: "bounce",
    bounce_type: $bounce_type,
    reason: $reason,
    occurred_at: $now
})
CREATE (s)-[:LOGGED]->(e)
RETURN s.email, s.status;
```

**Parameters:** `$email`, `$bounce_type`, `$reason`, `$now` (ISO timestamp from Python)

### Record Complaint

```ngql
MATCH (s:Subscriber {email: $email})
SET s.status = "complained"
CREATE (e:Event {type: "complaint", reason: $reason, occurred_at: $now})
CREATE (s)-[:LOGGED]->(e)
RETURN s.email;
```

**Parameters:** `$email`, `$reason`, `$now` (ISO timestamp from Python)

---

## Interest Inference

### Calculate Subscriber Interests

Aggregates click behavior to infer topic interests.

```ngql
MATCH (s:Subscriber {email: $email})-[c:CLICKED]->(l:Link)-[:ABOUT]->(t:Topic)
WITH s, t, SUM(c.click_count) AS total_clicks, MAX(c.clicked_at) AS last_click
MERGE (s)-[i:INTERESTED_IN]->(t)
SET i.score = total_clicks, i.last_updated = $now
RETURN t.name, i.score, last_click
ORDER BY i.score DESC;
```

**Parameters:** `$email`, `$now` (ISO timestamp from Python)

### Batch Recalculate All Interests

```ngql
MATCH (s:Subscriber)-[c:CLICKED]->(l:Link)-[:ABOUT]->(t:Topic)
WHERE s.status = "active"
WITH s, t, SUM(c.click_count) AS total_clicks
MERGE (s)-[i:INTERESTED_IN]->(t)
SET i.score = total_clicks, i.last_updated = $now
RETURN COUNT(DISTINCT s) AS subscribers_updated;
```

**Parameters:** `$now` (ISO timestamp from Python)

### Get Subscribers Interested in Topic

```ngql
MATCH (s:Subscriber)-[i:INTERESTED_IN]->(t:Topic {slug: $topic_slug})
WHERE s.status = "active"
RETURN s.email, s.name, i.score
ORDER BY i.score DESC
LIMIT 50;
```

**Parameters:** `$topic_slug`

### Content Recommendations (Collaborative Filtering)

Recommends content based on what similar subscribers have clicked.

```ngql
MATCH (s:Subscriber {email: $email})-[:INTERESTED_IN]->(t:Topic)
WITH s, COLLECT(t) AS my_topics
MATCH (other:Subscriber)-[:INTERESTED_IN]->(t:Topic)
WHERE other <> s AND t IN my_topics AND other.status = "active"
WITH s, other, COUNT(t) AS shared_topics
WHERE shared_topics >= 2
MATCH (other)-[:CLICKED]->(l:Link)
WHERE NOT EXISTS((s)-[:CLICKED]->(l))
RETURN l.title, l.url, COUNT(DISTINCT other) AS recommended_by
ORDER BY recommended_by DESC
LIMIT 5;
```

**Parameters:** `$email`

### Find Inactive Subscribers

Subscribers with no opens in the last 90 days.

```ngql
MATCH (s:Subscriber)
WHERE s.status = "active"
OPTIONAL MATCH (s)-[r:RECEIVED]->(n:Newsletter)
WHERE r.opened_at IS NOT NULL AND r.opened_at > $cutoff
WITH s, COUNT(r) AS recent_opens
WHERE recent_opens = 0
RETURN s.email, s.name, s.confirmed_at
ORDER BY s.confirmed_at DESC;
```

**Parameters:** `$cutoff` (ISO timestamp from Python: `datetime.utcnow() - timedelta(days=90)`)

---

## Analytics

### Newsletter Performance

```ngql
MATCH (n:Newsletter)
WHERE n.sent_at IS NOT NULL
OPTIONAL MATCH (s:Subscriber)-[r:RECEIVED]->(n)
WITH n,
     COUNT(r) AS sent,
     SUM(CASE WHEN r.opened_at IS NOT NULL THEN 1 ELSE 0 END) AS opens,
     SUM(COALESCE(r.click_count, 0)) AS clicks
RETURN n.slug, n.subject, n.sent_at,
       sent, opens, clicks,
       CASE WHEN sent > 0 THEN toFloat(opens) / sent * 100 ELSE 0 END AS open_rate,
       CASE WHEN opens > 0 THEN toFloat(clicks) / opens * 100 ELSE 0 END AS click_to_open_rate
ORDER BY n.sent_at DESC;
```

### Top Performing Links

```ngql
MATCH (l:Link)<-[c:CLICKED]-(s:Subscriber)
RETURN l.url, l.title, l.domain,
       COUNT(DISTINCT s) AS unique_clickers,
       SUM(c.click_count) AS total_clicks
ORDER BY total_clicks DESC
LIMIT 20;
```

### Topic Engagement

```ngql
MATCH (t:Topic)<-[:ABOUT]-(l:Link)<-[c:CLICKED]-(s:Subscriber)
RETURN t.name, t.slug,
       COUNT(DISTINCT s) AS unique_clickers,
       SUM(c.click_count) AS total_clicks
ORDER BY total_clicks DESC;
```

### Subscriber Growth Over Time

```ngql
MATCH (s:Subscriber)
WHERE s.status = "active"
RETURN date(s.confirmed_at) AS date, COUNT(s) AS new_subscribers
ORDER BY date DESC
LIMIT 30;
```

### Bounce Rate by Newsletter

```ngql
MATCH (n:Newsletter)<-[r:RECEIVED]-(s:Subscriber)
WHERE n.sent_at IS NOT NULL
WITH n,
     COUNT(r) AS sent,
     SUM(CASE WHEN r.delivery_status = "bounced" THEN 1 ELSE 0 END) AS bounced
RETURN n.slug, n.subject, sent, bounced,
       CASE WHEN sent > 0 THEN toFloat(bounced) / sent * 100 ELSE 0 END AS bounce_rate
ORDER BY n.sent_at DESC;
```

### Recent Events

```ngql
MATCH (s:Subscriber)-[:LOGGED]->(e:Event)
RETURN s.email, e.type, e.occurred_at, e.reason
ORDER BY e.occurred_at DESC
LIMIT 50;
```

---

## Full-Text Search

### Search Newsletters

```ngql
CALL neural.fulltext.query('newsletter_search', $query) YIELD node, score
RETURN node.slug, node.subject, score
ORDER BY score DESC
LIMIT 10;
```

**Parameters:** `$query`

### Search Subscribers

```ngql
CALL neural.fulltext.query('subscriber_search', $query) YIELD node, score
RETURN node.email, node.name, score
ORDER BY score DESC
LIMIT 10;
```

**Parameters:** `$query`

### Search Links

```ngql
CALL neural.fulltext.query('link_search', $query) YIELD node, score
RETURN node.url, node.title, score
ORDER BY score DESC
LIMIT 10;
```

**Parameters:** `$query`
