# Integration Guide

This guide covers how to integrate with the NeuralGraph Newsletter API from various platforms and use cases.

## Table of Contents

- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Common Integrations](#common-integrations)
  - [Website Integration](#website-integration)
  - [Mobile App Integration](#mobile-app-integration)
  - [Admin Dashboard](#admin-dashboard)
  - [CI/CD Pipeline](#cicd-pipeline)
- [Webhooks](#webhooks)
- [API Examples](#api-examples)
- [SDKs & Libraries](#sdks--libraries)

---

## Authentication

The API uses two authentication methods:

### JWT Tokens (For Users/Sessions)

```bash
# 1. Login to get token
curl -X POST https://api.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response:
# {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400}

# 2. Use token in requests
curl https://api.example.com/newsletters/ \
  -H "Authorization: Bearer eyJ..."
```

**Token lifetime:** 24 hours

### API Keys (For Services/Automation)

```bash
# Use API key directly
curl https://api.example.com/newsletters/ \
  -H "Authorization: Bearer nk_your-api-key"
```

**API key format:** `nk_` prefix followed by random string

### Public Endpoints (No Auth Required)

| Endpoint | Description |
|----------|-------------|
| `POST /subscribers/subscribe` | New subscription |
| `POST /subscribers/confirm` | Confirm email |
| `POST /subscribers/unsubscribe` | Unsubscribe |
| `GET /track/open/{slug}/{email}` | Tracking pixel |
| `GET /track/click` | Click tracking |
| `GET /health/*` | Health checks |

---

## Quick Start

### 1. Subscribe a User (Public)

Sends a confirmation email. After confirmation, a welcome email is sent automatically.

```javascript
// No authentication required
const response = await fetch('https://api.example.com/subscribers/subscribe', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    name: 'John Doe'
  })
});

const result = await response.json();
// { "message": "Please check your email to confirm subscription.", "success": true }
```

### 2. Create a Newsletter (Admin)

```javascript
const response = await fetch('https://api.example.com/newsletters/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`
  },
  body: JSON.stringify({
    slug: 'issue-42',
    subject: 'Weekly Update #42',
    content_md: `# This Week

Welcome to issue 42!

## Highlights

- New feature launched
- Bug fixes
- Performance improvements

## Featured Article

Check out our [latest blog post](https://example.com/blog).

\`\`\`javascript
// Code example
console.log('Hello Newsletter!');
\`\`\`
`
  })
});
```

### 3. Send Newsletter (Admin)

Sends emails to all active subscribers via Resend and creates delivery records.

```javascript
const result = await fetch('https://api.example.com/newsletters/issue-42/send', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${API_KEY}` }
});
// { "message": "Newsletter sent to 150 subscribers", "success": true }
```

---

## Common Integrations

### Website Integration

#### Subscription Form (HTML + JavaScript)

```html
<form id="subscribe-form">
  <input type="email" id="email" placeholder="your@email.com" required>
  <input type="text" id="name" placeholder="Your Name" required>
  <button type="submit">Subscribe</button>
  <p id="message"></p>
</form>

<script>
const API_URL = 'https://api.example.com';

document.getElementById('subscribe-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const name = document.getElementById('name').value;
  const message = document.getElementById('message');

  try {
    const res = await fetch(`${API_URL}/subscribers/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, name })
    });

    const data = await res.json();

    if (res.ok) {
      message.textContent = '✓ Check your email to confirm!';
      message.style.color = 'green';
    } else {
      message.textContent = data.detail || 'Something went wrong';
      message.style.color = 'red';
    }
  } catch (err) {
    message.textContent = 'Network error. Please try again.';
    message.style.color = 'red';
  }
});
</script>
```

#### React Component

```jsx
import { useState } from 'react';

const API_URL = process.env.REACT_APP_NEWSLETTER_API;

export function SubscribeForm() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/subscribers/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name })
      });

      const data = await res.json();

      if (res.ok) {
        setStatus({ type: 'success', message: 'Check your email to confirm!' });
        setEmail('');
        setName('');
      } else {
        setStatus({ type: 'error', message: data.detail });
      }
    } catch {
      setStatus({ type: 'error', message: 'Network error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Subscribing...' : 'Subscribe'}
      </button>
      {status.message && (
        <p className={status.type}>{status.message}</p>
      )}
    </form>
  );
}
```

### Mobile App Integration

#### Swift (iOS)

```swift
import Foundation

class NewsletterAPI {
    static let baseURL = "https://api.example.com"

    static func subscribe(email: String, name: String) async throws -> Bool {
        let url = URL(string: "\(baseURL)/subscribers/subscribe")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["email": email, "name": name]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            return false
        }

        return httpResponse.statusCode == 200
    }
}

// Usage
Task {
    let success = try await NewsletterAPI.subscribe(
        email: "user@example.com",
        name: "John Doe"
    )
}
```

#### Kotlin (Android)

```kotlin
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

object NewsletterAPI {
    private const val BASE_URL = "https://api.example.com"
    private val client = OkHttpClient()
    private val JSON = "application/json".toMediaType()

    suspend fun subscribe(email: String, name: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("email", email)
                put("name", name)
            }

            val request = Request.Builder()
                .url("$BASE_URL/subscribers/subscribe")
                .post(json.toString().toRequestBody(JSON))
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                Result.success("Check your email to confirm!")
            } else {
                val error = JSONObject(response.body?.string() ?: "{}")
                Result.failure(Exception(error.optString("detail", "Error")))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### Admin Dashboard

#### Python Admin Client

```python
import httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class NewsletterClient:
    base_url: str
    api_key: str

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    async def list_newsletters(self, sent_only: bool = False):
        async with httpx.AsyncClient() as client:
            params = {"sent_only": sent_only} if sent_only else {}
            response = await client.get(
                f"{self.base_url}/newsletters/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def create_newsletter(
        self,
        slug: str,
        subject: str,
        content_md: str,
        preview_text: Optional[str] = None
    ):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/newsletters/",
                headers=self.headers,
                json={
                    "slug": slug,
                    "subject": subject,
                    "content_md": content_md,
                    "preview_text": preview_text
                }
            )
            response.raise_for_status()
            return response.json()

    async def send_newsletter(self, slug: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/newsletters/{slug}/send",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_analytics(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics/subscribers/summary",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    client = NewsletterClient(
        base_url="https://api.example.com",
        api_key="nk_your-api-key"
    )

    # Create newsletter
    await client.create_newsletter(
        slug="weekly-42",
        subject="Weekly Update #42",
        content_md="# Hello\n\nThis is the newsletter content."
    )

    # Send it
    result = await client.send_newsletter("weekly-42")
    print(result)  # {"message": "Newsletter sent to 150 subscribers", "success": true}
```

### CI/CD Pipeline

#### GitHub Actions - Auto-publish Newsletter

```yaml
# .github/workflows/publish-newsletter.yml
name: Publish Newsletter

on:
  push:
    paths:
      - 'newsletters/*.md'
    branches:
      - main

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get changed files
        id: changed
        uses: tj-actions/changed-files@v41
        with:
          files: newsletters/*.md

      - name: Publish newsletters
        if: steps.changed.outputs.any_changed == 'true'
        env:
          API_URL: ${{ secrets.NEWSLETTER_API_URL }}
          API_KEY: ${{ secrets.NEWSLETTER_API_KEY }}
        run: |
          for file in ${{ steps.changed.outputs.all_changed_files }}; do
            # Extract slug from filename (e.g., newsletters/2024-01-issue-42.md -> 2024-01-issue-42)
            slug=$(basename "$file" .md)

            # Extract subject from first H1
            subject=$(grep -m1 '^# ' "$file" | sed 's/^# //')

            # Get content
            content=$(cat "$file")

            # Create/update newsletter
            curl -X POST "$API_URL/newsletters/" \
              -H "Authorization: Bearer $API_KEY" \
              -H "Content-Type: application/json" \
              -d "{
                \"slug\": \"$slug\",
                \"subject\": \"$subject\",
                \"content_md\": $(echo "$content" | jq -Rs .)
              }"
          done
```

---

## Webhooks

### Email Provider Webhooks (Resend)

Configure your email provider to send webhooks to these endpoints:

```
POST /track/bounce
POST /track/complaint
```

#### Resend Webhook Example

```javascript
// Express.js webhook handler
app.post('/webhooks/resend', express.json(), async (req, res) => {
  const { type, data } = req.body;

  if (type === 'email.bounced') {
    await fetch(`${NEWSLETTER_API}/track/bounce`, {
      method: 'POST',
      params: new URLSearchParams({
        email: data.to,
        newsletter_slug: data.tags?.newsletter_slug || 'unknown',
        reason: data.bounce?.message || 'unknown'
      })
    });
  }

  if (type === 'email.complained') {
    await fetch(`${NEWSLETTER_API}/track/complaint`, {
      method: 'POST',
      params: new URLSearchParams({
        email: data.to,
        feedback_type: 'spam'
      })
    });
  }

  res.status(200).send('OK');
});
```

---

## API Examples

### cURL Examples

```bash
# Set your API key
export API_KEY="nk_your-api-key"
export API_URL="https://api.example.com"

# Subscribe (no auth)
curl -X POST "$API_URL/subscribers/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "John Doe"}'

# List newsletters
curl "$API_URL/newsletters/" \
  -H "Authorization: Bearer $API_KEY"

# Create newsletter with markdown
curl -X POST "$API_URL/newsletters/" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "issue-42",
    "subject": "Weekly Update",
    "content_md": "# Hello\n\nWelcome to the newsletter!"
  }'

# Preview newsletter HTML
curl "$API_URL/newsletters/issue-42/preview" \
  -H "Authorization: Bearer $API_KEY"

# Update newsletter
curl -X PUT "$API_URL/newsletters/issue-42" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content_md": "# Updated\n\nNew content here."}'

# Send newsletter
curl -X POST "$API_URL/newsletters/issue-42/send" \
  -H "Authorization: Bearer $API_KEY"

# Get analytics
curl "$API_URL/analytics/subscribers/summary" \
  -H "Authorization: Bearer $API_KEY"

curl "$API_URL/analytics/newsletters/performance" \
  -H "Authorization: Bearer $API_KEY"
```

### JavaScript/TypeScript SDK

```typescript
class NewsletterSDK {
  constructor(
    private baseUrl: string,
    private apiKey?: string
  ) {}

  private async request(
    path: string,
    options: RequestInit = {}
  ): Promise<any> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // Public methods
  async subscribe(email: string, name: string) {
    return this.request('/subscribers/subscribe', {
      method: 'POST',
      body: JSON.stringify({ email, name }),
    });
  }

  async confirm(token: string) {
    return this.request('/subscribers/confirm', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async unsubscribe(email: string) {
    return this.request('/subscribers/unsubscribe', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  // Admin methods (require API key)
  async listNewsletters(sentOnly = false) {
    const params = sentOnly ? '?sent_only=true' : '';
    return this.request(`/newsletters/${params}`);
  }

  async createNewsletter(data: {
    slug: string;
    subject: string;
    content_md?: string;
    preview_text?: string;
  }) {
    return this.request('/newsletters/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateNewsletter(slug: string, data: {
    subject?: string;
    content_md?: string;
    preview_text?: string;
  }) {
    return this.request(`/newsletters/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async sendNewsletter(slug: string) {
    return this.request(`/newsletters/${slug}/send`, {
      method: 'POST',
    });
  }

  async getAnalytics() {
    return {
      subscribers: await this.request('/analytics/subscribers/summary'),
      performance: await this.request('/analytics/newsletters/performance'),
    };
  }
}

// Usage
const sdk = new NewsletterSDK('https://api.example.com', 'nk_your-api-key');

// Subscribe (works without API key too)
await sdk.subscribe('user@example.com', 'John');

// Admin operations
await sdk.createNewsletter({
  slug: 'issue-42',
  subject: 'Weekly Update',
  content_md: '# Hello World',
});

await sdk.sendNewsletter('issue-42');
```

---

## SDKs & Libraries

### Official SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python | `neuralgraph-newsletter` | `pip install neuralgraph-newsletter` |
| JavaScript | `@neuralgraph/newsletter` | `npm install @neuralgraph/newsletter` |

*Coming soon*

### Community SDKs

*None yet - contributions welcome!*

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /subscribers/subscribe` | 5 requests | 1 minute |
| `POST /auth/login` | 5 requests | 5 minutes |
| Other endpoints | 10 requests | 1 minute |

When rate limited, you'll receive:
```json
{
  "detail": "Too many requests. Try again in 45 seconds."
}
```

With header: `Retry-After: 45`

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 422 | Validation error (check request body) |
| 429 | Rate limited |
| 500 | Server error |

---

## Support

- **Documentation:** [README.md](../README.md)
- **API Reference:** `https://api.example.com/docs` (Swagger UI)
- **Issues:** [GitHub Issues](https://github.com/neuralgraph/neuralgraph-newsletter/issues)
