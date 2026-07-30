# Client Callback Setup

This guide walks through running an example webhook client and using it to receive notifications of completed reviews from PathReview.

The client here can be any external service that you run to receive PathReview's webhook notifications, by listening on a URL you register via the [Webhooks API](API.md#webhooks). 

In [`docs/examples/client_callback_server.py`](examples/client_callback_server.py), we have provided a runnable, self-contained example implementation built with FastAPI.

> **Note:** This file is a barebones example for local testing/demonstration only. PathReview does not provide a real client implementation; you are responsible for building and testing your own.

## Prerequisites

Complete [SETUP.md](SETUP.md) first and have the server running locally. This should set you up with a user, profile and some reviews.

## Getting a token

`POST /auth/login` takes form-encoded credentials (not JSON) and returns a JWT:

```bash
curl -X POST http://localhost:8000/auth/login \
    -d "username=user1@example.com&password=password1"
```

Response: `{"access_token": "...", "token_type": "bearer"}`.

All authenticated routes below (`/webhooks/callbacks`, `/reviews`) read this token through the `Authorization: Bearer <token>` header. Use the `access_token` as `<token>` in the examples below.

## What can the client do (general)

- `POST /register-callback` / `DELETE /delete-callback` — register a callback URL that receives the notifications and delete them anytime. Note that one cannot update the existing entry; you must delete it the existing entry first.
- Any API/endpoint that can receive the notification payload and acknowledge it.
- Dedup by `notification_id` — PathReview provides a way to handle idempotency on the client side using `notification_id`
  in the example it uses an in-memory db to save the id; a real client should persist this, e.g. a unique index in its own DB.


The notification payload shape (sent by `send_notification` in
`core/services/webhook_service.py`):

```json
{
    "notification_id": "...",
    "review_id": "...",
    "callback_id": "...",
    "event": "review.completed"
}
```

## Step by step client setup

1. Start the example client:

   ```bash
   python docs/examples/client_callback_server.py
   ```

   This runs on `http://localhost:9000`.

2. Get a `profile_id`. `make setup` seeds one or more profiles per user
   (`user1@example.com` / `user2@example.com` / `user3@example.com`) — pick one belonging to whichever user you logged in as in the previous step. Use the email of that user to get the `profile_id`:

   ```bash
   docker compose exec db psql -U pathreview -d pathreview_dev -c \
       "SELECT p.id, u.email FROM profiles p JOIN users u ON u.id = p.user_id WHERE u.email = 'user1@example.com';"
   ```

   You can also create a new profile with `POST /profiles` (only `github_username`/`portfolio_url`/`resume_file` are accepted, and all are optional):

   ```bash
   curl -X POST http://localhost:8000/profiles \
       -H "Authorization: Bearer <token>" \
       -F "github_username=someuser"
   ```

3. Register its `/callback` URL for that profile. Only one callback is allowed per profile — if you've already registered one for this profile (e.g. from a previous run of this guide), this returns `409 Conflict`; delete it first (Step 5) before re-registering. 

You can directly do this against PathReview's API:

   ```bash
   curl -X POST http://localhost:8000/webhooks/callbacks \
       -H "Authorization: Bearer <token>" \
       -H "Content-Type: application/json" \
       -d '{"profile_id": "...", "url": "http://localhost:9000/callback"}'
   ```

   ...or via the example client's own convenience route:

   ```bash
   curl -X POST http://localhost:9000/register-callback \
       -H "Content-Type: application/json" \
       -d '{"pathreview_base_url": "http://localhost:8000", "token": "<token>", "profile_id": "..."}'
   ```

4. Request a review for that profile:

   ```bash
   curl -X POST http://localhost:8000/reviews \
       -H "Authorization: Bearer <token>" \
       -H "Content-Type: application/json" \
       -d '{"profile_id": "..."}'
   ```

   Once processing completes, the example client logs the received notification:

   ```
   [received] notification_id=... review_id=... callback_id=... event=review.completed
   ```

5. You can delete the callback entry when done, either directly:

   ```bash
   curl -X DELETE http://localhost:8000/webhooks/callbacks/<profile_id> \
       -H "Authorization: Bearer <token>"
   ```

   ...or via the example client:

   ```bash
   curl -X DELETE http://localhost:9000/delete-callback \
       -H "Content-Type: application/json" \
       -d '{"pathreview_base_url": "http://localhost:8000", "token": "<token>", "profile_id": "..."}'
   ```
