## Solution plan

**Issue:** Implement a webhook system that notifies users when their review is ready ([#87](https://github.com/ascherj/pathreview/issues/87))

### Understand

There's no root-cause bug here: this is a missing feature. Expected behavior: a client that kicks off a multi-repo review (which takes 30-90 seconds) should be able to register a callback URL once, then get a `POST` with the completed review payload when it's done, instead of having to poll.

Actual behavior, confirmed by reproduction: `POST /reviews` (`api/routes/reviews.py:22-62`) creates the review, schedules `process_review` as a FastAPI `BackgroundTasks` job (line 43), and returns `status="pending"` immediately. `process_review` (`core/services/review_service.py:82-195`) runs ingestion, agent orchestration, RAG, and safety checks, then sets `review.status = "complete"` (line 168) or `"failed"` (line 189) and commits. At no point does anything get sent anywhere; the only way a client can learn the review finished is by repeatedly calling `GET /reviews/{id}/status` (`api/routes/reviews.py:139-176`). I confirmed this gap locally by registering a user, creating a profile, creating a review, and watching it flip to `"complete"` in the logs with zero outbound notification, only discoverable by manually polling the status endpoint (see JOURNAL.md for the full reproduction steps).

### Map

Files I expect to touch:

- **`core/models/webhook.py`** (new): `Webhook` model with `id`, `user_id` (FK to `users`, CASCADE), `url` (String(500), matching the existing `portfolio_url`/`source_url` convention in `core/models/profile.py:33` and `core/models/ingested_source.py`), `secret` (for HMAC signing), `is_active`, `created_at`/`updated_at`. Follows the UUID-PK plus `TYPE_CHECKING`-guarded relationship pattern used in `core/models/review.py:17-54`.
- **`core/models/webhook_delivery.py`** (new, or folded into the same file): `WebhookDelivery` log with `id`, `webhook_id` (FK), `review_id` (FK), `status` (`"pending"`/`"success"`/`"failed"`), `attempt_count`, `last_attempted_at`, `response_status_code`. Needed so retries and delivery history are inspectable, not just fire-and-forget.
- **`core/models/__init__.py`**: export the two new models alongside `Base, User, Profile, IngestedSource, Review`.
- **`core/services/webhook_service.py`** (new): module-level async functions (matching the style of `core/services/review_service.py`, not a class): `register_webhook`, `list_webhooks`, `delete_webhook`, `deliver_webhook_notification(db, review_id)`, plus a private `_send_with_retry` helper. `structlog` logger at module scope, `db` as first positional arg everywhere, per the existing convention.
- **`api/routes/webhooks.py`** (new): `router = APIRouter(prefix="/webhooks", tags=["webhooks"])`, endpoints for `POST /webhooks` (register), `GET /webhooks` (list), `DELETE /webhooks/{id}` (deregister). Mirrors the structure of `api/routes/reviews.py` (try/except into `HTTPException`, `structlog` logging, `Depends(get_current_user)`, `Depends(get_db)`).
- **`api/schemas/webhook.py`** (new): `WebhookCreate`, `WebhookResponse` pydantic schemas, matching `api/schemas/review.py`'s pattern.
- **`api/main.py`**: add `webhooks` to the router import on line 8 and `app.include_router(webhooks.router)` alongside line 82.
- **`core/services/review_service.py`**: call `webhook_service.deliver_webhook_notification(db, review_id)` at both the success commit (currently line 174) and the failure commit (around line 192).
- **`alembic/versions/003_add_webhooks.py`** (new): follows the exact structure of `002_add_error_message_to_reviews.py`, with numeric revision id `"003"`, `down_revision = "002"`, `op.create_table` for both new tables with named constraints (matching `001_initial_schema.py`'s `op.f("fk_...")` style).
- **`core/config.py`**: add webhook-related settings (delivery timeout, max retry attempts) under a new `# Webhooks` comment section, following the existing `# Feature Limits` / `# Rate Limiting` grouping style (lines ~34-40).
- **`tests/unit/test_webhook_service.py`** (new): mirrors `tests/unit/test_review_service.py`'s structure, with an `@pytest.mark.unit` class, `AsyncMock` DB session fixture, `unittest.mock.patch` on the ORM model class. Since no httpx mocking precedent exists anywhere in the repo yet (confirmed via grep; `pytest-httpserver` is a declared dependency but unused), this file will be the first to actually use it for mocking the outbound webhook POST.

### Plan

1. **Add the data layer**: create `Webhook` and `WebhookDelivery` models plus the Alembic migration (`003_add_webhooks.py`), run `alembic upgrade head` locally and confirm the tables exist via `psql`.
2. **Build `webhook_service.py`**: implement `register_webhook`/`list_webhooks`/`delete_webhook` (straightforward CRUD against the new table) first, since they're low-risk and testable in isolation.
3. **Build delivery logic**: implement `deliver_webhook_notification(db, review_id)` using `httpx.AsyncClient` (the codebase currently only uses sync `httpx.get`/`httpx.head` in `agent/tools/github_tool.py`, so this introduces the first async HTTP client usage) with HMAC-SHA256 request signing (secret stored on the `Webhook` row) and a `tenacity`-based retry with exponential backoff (the dependency is already declared in `pyproject.toml:33` but currently unused anywhere; this would be the first real use of it).
4. **Wire it into `process_review`**: add the two call sites in `core/services/review_service.py` (success path around line 174, failure path around line 192), passing `review_id` so the service can look up all active webhooks for that review's owning user and fan out.
5. **Add the API surface**: `api/routes/webhooks.py` plus `api/schemas/webhook.py` plus registration in `api/main.py`, then write `tests/unit/test_webhook_service.py` covering registration, successful delivery, retry-then-succeed, and retry-exhausted-then-log-failure.

### Inputs & outputs

- **Registration input**: `POST /webhooks` body `{ "url": "https://client.example.com/callback" }` (authenticated via existing `Depends(get_current_user)`), output: `WebhookResponse` with the generated `id` and a one-time-visible `secret` for HMAC verification.
- **Delivery input**: internally, `deliver_webhook_notification(db, review_id)` takes a completed/failed `Review` row plus the set of `Webhook` rows for `review.profile.user_id`.
- **Delivery output**: an outbound `POST` to each registered `url` with a JSON body shaped like the existing `ReviewResponse` schema (`{review_id, status, sections, overall_score, error_message}`) plus an `X-PathReview-Signature` header (HMAC of the body using the webhook's `secret`). Side effect: a `WebhookDelivery` row is written recording the attempt outcome (status code, attempt count), a new persisted side effect that didn't exist before.

### Risks & unknowns

- **Stale `db` session in the background task**: `process_review` receives the same `AsyncSession` that was created for the original request (`api/routes/reviews.py:43`, passed straight into `background_tasks.add_task`). Adding webhook delivery (another async operation) into that same task risks fighting over an already-borderline session lifetime, so it's worth checking whether `get_db()`'s session (`core/database.py`) actually survives long enough for a 30-90s job before I add more work onto it, or whether webhook delivery needs its own session scope.
- **No async httpx precedent**: `agent/tools/github_tool.py` only uses sync `httpx.get`/`.head` with hardcoded timeouts (10s/5s). There's no existing settings-driven timeout or async client pattern to copy, so I'm introducing that convention fresh and need to pick sane defaults (likely a short delivery timeout, e.g. 5-10s, so one slow client callback can't stall the whole review pipeline).
- **Unverified `tenacity` usage**: it's a listed dependency (`pyproject.toml:33`) but grep found no actual import/usage anywhere in the app. I need to confirm the version installed actually supports the async retry decorator I'm planning to use (`tenacity.retry` with `wait_exponential`) before committing to it.
- **SSRF risk on registered URLs**: since `url` is arbitrary client input, a malicious registration could point at internal infra (e.g. `http://localhost:5433` or a metadata endpoint). I need to decide whether to validate/block private IP ranges at registration time; unresolved, will confirm with mentor/instructor before finalizing.
- **`/health` endpoint bugs are unrelated but adjacent**: while reproducing, I found the existing `/health` route has two pre-existing bugs (raw `"SELECT 1"` not wrapped in `sqlalchemy.text()`, and a reference to a non-existent `settings.redis_host`). These are out of scope for #87 but worth noting since a webhook health/status check might be tempted to reuse that pattern; I won't copy it as-is.

### Edge cases

- **Client's callback URL is unreachable or times out**: delivery must retry with backoff (via `tenacity`) and eventually give up, logging a `WebhookDelivery` row with `status="failed"` rather than crashing `process_review` or leaving the review stuck.
- **Review fails (`status="failed"`) rather than completing**: the webhook must still fire, carrying the failure state and `error_message`, not just the happy path. This is why both commit sites in `review_service.py` need the call, not just the success one.
- **User has zero registered webhooks**: `deliver_webhook_notification` should no-op cleanly (empty list, nothing to send) rather than erroring.
- **User has multiple registered webhooks for the same review**: all active ones should receive the POST independently; one failing shouldn't block delivery to the others.
- **Duplicate/malformed registration**: registering the same URL twice, or a non-HTTP(S) URL, should be rejected at the `POST /webhooks` validation layer (pydantic `HttpUrl` type) before it ever reaches the service layer.
- **Webhook deleted mid-flight**: if a user deletes a webhook after a review started processing but before it completes, delivery should just skip it (query active webhooks at delivery time, not at review-creation time).
