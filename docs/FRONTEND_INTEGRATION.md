# Frontend Integration Guide

Base URL: `https://neuralgraph.dev/api/newsletter`

## Authentication

### Public Endpoints (No Auth Required)
- `POST /subscribers/subscribe`
- `POST /subscribers/confirm`
- `POST /subscribers/unsubscribe`
- `GET /health`

### Protected Endpoints (Require API Key)
All other endpoints require the `Authorization` header:

```
Authorization: Bearer nk_your-api-key
```

---

## Subscriber Endpoints

### Subscribe (Public)

Creates a pending subscription and sends confirmation email.

```
POST /subscribers/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**Response (200):**
```json
{
  "message": "Please check your email to confirm subscription.",
  "success": true
}
```

**Errors:**
- `400` - Email already subscribed or confirmation pending
- `422` - Invalid email format
- `429` - Rate limited (5 requests/minute)

**Frontend Example (React):**
```jsx
async function subscribe(email, name) {
  const response = await fetch('https://neuralgraph.dev/api/newsletter/subscribers/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Subscription failed');
  }

  return data;
}
```

---

### Confirm Subscription (Public)

Confirms email subscription via token from confirmation email.

```
POST /subscribers/confirm
Content-Type: application/json

{
  "token": "abc123..."
}
```

**Response (200):**
```json
{
  "message": "Subscription confirmed!",
  "success": true
}
```

**Errors:**
- `400` - Invalid or expired token

**Frontend Example:**
```jsx
// Typically called from a /confirm?token=xxx page
async function confirmSubscription(token) {
  const response = await fetch('https://neuralgraph.dev/api/newsletter/subscribers/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  return response.json();
}

// In your confirm page component:
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  if (token) {
    confirmSubscription(token);
  }
}, []);
```

---

### Unsubscribe (Public)

```
POST /subscribers/unsubscribe
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Successfully unsubscribed",
  "success": true
}
```

---

## Newsletter Endpoints (Protected)

All require `Authorization: Bearer <api-key>`

### List Newsletters

```
GET /newsletters/
GET /newsletters/?sent_only=true
```

**Response:**
```json
[
  {
    "n.slug": "issue-42",
    "n.subject": "Weekly Update #42",
    "n.preview_text": "This week's highlights...",
    "n.created_at": "2026-01-15T10:00:00Z",
    "n.sent_at": "2026-01-15T12:00:00Z",
    "n.external_url": "https://neuralgraph.dev/newsletter/42"
  }
]
```

---

### Get Newsletter

```
GET /newsletters/{slug}
```

**Response:**
```json
{
  "n.slug": "issue-42",
  "n.subject": "Weekly Update #42",
  "n.preview_text": "This week's highlights...",
  "n.content_md": "# Hello\n\nNewsletter content...",
  "n.content_html": "<h1>Hello</h1><p>Newsletter content...</p>",
  "n.created_at": "2026-01-15T10:00:00Z",
  "n.sent_at": null,
  "links": [
    {"url": "https://example.com/article", "title": "Great Article"}
  ],
  "topics": ["rust", "performance"]
}
```

---

### Create Newsletter

```
POST /newsletters/
Content-Type: application/json

{
  "slug": "issue-43",
  "subject": "Weekly Update #43",
  "content_md": "# Hello\n\nThis is the newsletter content in **markdown**.",
  "preview_text": "Optional preview text",
  "external_url": "https://neuralgraph.dev/newsletter/43"
}
```

**Response:**
```json
{
  "message": "Newsletter 'issue-43' created",
  "success": true
}
```

---

### Update Newsletter (Draft Only)

```
PUT /newsletters/{slug}
Content-Type: application/json

{
  "subject": "Updated Subject",
  "content_md": "# Updated Content",
  "preview_text": "Updated preview"
}
```

---

### Preview Newsletter HTML

```
GET /newsletters/{slug}/preview
```

Returns rendered HTML page for preview.

---

### Send Newsletter

Sends newsletter to all active subscribers.

```
POST /newsletters/{slug}/send
```

**Response:**
```json
{
  "message": "Newsletter sent to 150 subscribers",
  "success": true
}
```

---

### Delete Newsletter (Draft Only)

```
DELETE /newsletters/{slug}
```

---

### Add Link to Newsletter

```
POST /newsletters/{slug}/links
Content-Type: application/json

{
  "url": "https://example.com/article",
  "title": "Article Title",
  "description": "Article description",
  "topic_slugs": ["rust", "performance"]
}
```

---

## Analytics Endpoints (Protected)

### Subscriber Summary

```
GET /analytics/subscribers/summary
```

**Response:**
```json
[
  {"status": "active", "count": 150},
  {"status": "pending", "count": 12},
  {"status": "unsubscribed", "count": 8}
]
```

---

### Subscriber Growth

```
GET /analytics/subscribers/growth?days=30
```

---

### Newsletter Performance

```
GET /analytics/newsletters/performance?days=30
```

**Response:**
```json
[
  {
    "n.slug": "issue-42",
    "n.subject": "Weekly Update",
    "sent": 150,
    "opens": 89,
    "clicks": 34,
    "open_rate": 59.3,
    "click_rate": 38.2
  }
]
```

---

### Top Subscribers

```
GET /analytics/engagement/top-subscribers?limit=10
```

---

### Top Links

```
GET /analytics/engagement/top-links?limit=10
```

---

### Topic Engagement

```
GET /analytics/topics/engagement
```

---

## Admin Endpoints (Protected)

### List Subscribers

```
GET /subscribers/
GET /subscribers/?status=active
GET /subscribers/?status=pending&limit=50
```

---

### Get Subscriber

```
GET /subscribers/{email}
```

---

## API Client Example (TypeScript)

```typescript
const API_URL = 'https://neuralgraph.dev/api/newsletter';
const API_KEY = 'nk_your-api-key';

class NewsletterAPI {
  private headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`
  };

  // Public - no auth needed
  async subscribe(email: string, name: string) {
    const res = await fetch(`${API_URL}/subscribers/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, name })
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  }

  // Protected
  async getNewsletters(sentOnly = false) {
    const url = sentOnly ? `${API_URL}/newsletters/?sent_only=true` : `${API_URL}/newsletters/`;
    const res = await fetch(url, { headers: this.headers });
    return res.json();
  }

  async createNewsletter(data: {
    slug: string;
    subject: string;
    content_md: string;
    preview_text?: string;
  }) {
    const res = await fetch(`${API_URL}/newsletters/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  }

  async sendNewsletter(slug: string) {
    const res = await fetch(`${API_URL}/newsletters/${slug}/send`, {
      method: 'POST',
      headers: this.headers
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    return res.json();
  }

  async getAnalyticsSummary() {
    const res = await fetch(`${API_URL}/analytics/subscribers/summary`, {
      headers: this.headers
    });
    return res.json();
  }

  async getNewsletterPerformance(days = 30) {
    const res = await fetch(`${API_URL}/analytics/newsletters/performance?days=${days}`, {
      headers: this.headers
    });
    return res.json();
  }
}

export const api = new NewsletterAPI();
```

---

## React Hook Example

```typescript
import { useState } from 'react';

export function useSubscribe() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const subscribe = async (email: string, name: string) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('https://neuralgraph.dev/api/newsletter/subscribers/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name })
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Subscription failed');
        return false;
      }

      setSuccess(true);
      return true;
    } catch (err) {
      setError('Network error');
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { subscribe, loading, error, success };
}
```

**Usage:**
```jsx
function SubscribeForm() {
  const { subscribe, loading, error, success } = useSubscribe();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await subscribe(email, name);
  };

  if (success) {
    return <p>Check your email to confirm!</p>;
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={e => setName(e.target.value)} placeholder="Name" required />
      <input value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="Email" required />
      <button disabled={loading}>{loading ? 'Subscribing...' : 'Subscribe'}</button>
      {error && <p style={{color: 'red'}}>{error}</p>}
    </form>
  );
}
```

---

## Error Handling

All errors return:
```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (validation error) |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 422 | Validation error |
| 429 | Rate limited |
| 500 | Server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST /subscribers/subscribe` | 5/minute per IP |
| `POST /auth/login` | 5/5 minutes per IP |
| Other endpoints | 10/minute |

When rate limited:
```json
{
  "detail": "Too many requests. Try again in 45 seconds."
}
```

---

## CORS

The API allows requests from:
- `https://neuralgraph.dev`
- `https://www.neuralgraph.dev`

If you need additional origins, update `CORS_ORIGINS` in the API config.
