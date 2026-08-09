# Webhook System Implementation

## Overview

The webhook system enables real-time notifications to external services when portfolio reviews complete or fail. This is critical for the PathReview application because reviews can take 30-90 seconds to process, and clients need to know when results are ready without polling.

## Architecture

### Components

1. **Webhook Model** (`core/models/webhook.py`)
   - Stores webhook configurations per user
   - Tracks webhook status and failure metrics
   - Supports event filtering (comma-separated event list)

2. **Webhook Service** (`core/services/webhook_service.py`)
   - CRUD operations for webhook management
   - Webhook event triggering logic
   - HMAC-SHA256 signature generation for security
   - Automatic retry handling and failure tracking

3. **Webhook Routes** (`api/routes/webhooks.py`)
   - REST API endpoints for webhook management
   - Authentication and authorization
   - CRUD operations via HTTP

4. **Webhook Schemas** (`api/schemas/webhook.py`)
   - Request/response validation
   - Type-safe API contracts

### Data Flow

```
1. User registers webhook (POST /webhooks)
   └─> Webhook stored in database

2. Review processing starts (background task)
   └─> Runs ingestion, agent, RAG, safety checks
   └─> Updates review status

3. Review completes or fails
   └─> trigger_review_event() called
   └─> Get all webhooks for user + event
   └─> Send POST to each webhook URL
   └─> Update webhook status + failure count

4. Webhook receives POST with signed payload
   └─> Verifies signature using secret
   └─> Processes review data
```

## API Endpoints

### Register Webhook
```
POST /webhooks

Request:
{
  "url": "https://example.com/callback",
  "events": "review.completed,review.failed",
  "secret": "optional-signing-key",
  "description": "My webhook"
}

Response:
{
  "id": "webhook-uuid",
  "url": "https://example.com/callback",
  "events": "review.completed,review.failed",
  "is_active": true,
  "secret": "optional-signing-key",
  "description": "My webhook",
  "last_triggered_at": null,
  "last_status_code": null,
  "failure_count": 0,
  "created_at": "2026-03-23T...",
  "updated_at": "2026-03-23T..."
}
```

### List Webhooks
```
GET /webhooks?page=1&page_size=20

Response:
{
  "items": [...],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

### Get Webhook
```
GET /webhooks/{webhook_id}

Response: Single webhook object
```

### Update Webhook
```
PATCH /webhooks/{webhook_id}

Request (all fields optional):
{
  "url": "new-url",
  "events": "new-events",
  "secret": "new-secret",
  "description": "new-description",
  "is_active": true
}

Response: Updated webhook object
```

### Delete Webhook
```
DELETE /webhooks/{webhook_id}

Response: 204 No Content
```

## Webhook Events

### review.completed
Triggered when a portfolio review completes successfully.

```json
{
  "event": "review.completed",
  "webhook_id": "webhook-uuid",
  "timestamp": "2026-03-23T10:30:00",
  "data": {
    "review_id": "review-uuid",
    "profile_id": "profile-uuid",
    "status": "complete",
    "overall_score": 0.81,
    "sections": [
      {
        "section_name": "Technical Skills",
        "content": "Detailed feedback...",
        "confidence": 0.85,
        "suggestions": ["Suggestion 1", "Suggestion 2"]
      }
    ],
    "created_at": "2026-03-23T10:00:00",
    "updated_at": "2026-03-23T10:30:00"
  }
}
```

### review.failed
Triggered when a portfolio review fails during processing.

```json
{
  "event": "review.failed",
  "webhook_id": "webhook-uuid",
  "timestamp": "2026-03-23T10:30:00",
  "data": {
    "review_id": "review-uuid",
    "profile_id": "profile-uuid",
    "status": "failed",
    "error": "Error message describing what went wrong",
    "created_at": "2026-03-23T10:00:00",
    "updated_at": "2026-03-23T10:30:00"
  }
}
```

## Security

### Signature Verification

Each webhook is optionally signed using HMAC-SHA256 for security verification.

When a webhook has a configured secret:
1. The entire JSON payload is signed using the secret
2. The signature is sent in the `X-Webhook-Signature` header as `sha256=<hex-digest>`
3. The receiving service should verify the signature

Example verification in Python:
```python
import hmac
import hashlib
import json

def verify_webhook(payload_bytes, secret, signature_header):
    # Extract the hex digest from header (format: "sha256=...")
    expected_sig = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    header_sig = signature_header.split("=")[1]
    return hmac.compare_digest(expected_sig, header_sig)
```

### Best Practices

1. **Always verify signatures** when a secret is configured
2. **Use HTTPS only** for webhook URLs
3. **Set a secret** during webhook registration
4. **Handle timeouts** - webhook delivery has a 10-second timeout
5. **Implement idempotency** - webhooks may be retried on network failures

## Failure Handling

- Webhook delivery has a 10-second timeout
- If delivery fails (non-2xx status or timeout), `failure_count` increments
- `last_status_code` and `last_triggered_at` are updated after each attempt
- Webhooks with high failure counts can be disabled manually via `PATCH` endpoint
- No automatic retries are performed (future enhancement)

## Database Schema

```sql
CREATE TABLE webhooks (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  url VARCHAR(500) NOT NULL,
  events VARCHAR(255) NOT NULL DEFAULT 'review.completed',
  is_active BOOLEAN NOT NULL DEFAULT true,
  secret VARCHAR(255),
  description TEXT,
  last_triggered_at TIMESTAMP WITH TIME ZONE,
  last_status_code INTEGER,
  failure_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  
  INDEX ix_webhooks_user_id (user_id),
  INDEX ix_webhooks_is_active (is_active)
);
```

## Configuration

No special configuration needed. The webhook system is enabled by default and:
- Uses the same database connection as the main application
- Requires `httpx` for async HTTP client (already in dependencies)
- Uses `structlog` for logging (already configured)

## Testing

Unit tests are included in `tests/unit/test_webhooks.py`:

```bash
pytest tests/unit/test_webhooks.py
```

Integration tests can be created to test:
1. Webhook registration flow
2. Review processing with webhook triggers
3. Signature verification
4. Failure handling and retry logic

## Example Usage

### Register a Webhook
```bash
curl -X POST http://localhost:8000/webhooks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://my-service.com/pathreview-webhook",
    "events": "review.completed,review.failed",
    "secret": "my-secret-key",
    "description": "Trigger notifications when reviews complete"
  }'
```

### Handle Webhook in Your Service
```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json

app = FastAPI()

@app.post("/pathreview-webhook")
async def handle_webhook(request: Request):
    # Get the signature from headers
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Read the raw body
    body = await request.body()
    
    # Verify signature
    expected_sig = hmac.new(
        b"my-secret-key",
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, signature.split("=")[1]):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse the payload
    payload = json.loads(body)
    
    # Handle the event
    if payload["event"] == "review.completed":
        review_data = payload["data"]
        print(f"Review {review_data['review_id']} completed with score {review_data['overall_score']}")
    elif payload["event"] == "review.failed":
        review_data = payload["data"]
        print(f"Review {review_data['review_id']} failed: {review_data['error']}")
    
    return {"status": "ok"}
```

## Future Enhancements

1. **Automatic Retries** - Implement exponential backoff for failed deliveries
2. **Webhook History** - Store delivery logs for debugging
3. **Custom Headers** - Allow users to add custom headers to webhook requests
4. **Webhook Testing** - Endpoint to test webhook delivery
5. **Event Filtering** - More granular event filtering (e.g., only high-score completions)
6. **Rate Limiting** - Per-webhook rate limiting
7. **Batch Webhooks** - Send multiple events in a single payload

## Migration Notes

The webhook system requires running the database migration:

```bash
alembic upgrade 003
```

This creates the `webhooks` table and indexes for efficient querying by user and active status.
