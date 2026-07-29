## Week 7 - Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/87](https://github.com/ascherj/pathreview/issues/87)

**Issue title:** Implement a webhook system that notifies users when their review is ready #87

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
When users request AI reviews of multiple repositories, the process takes 30-90 seconds to complete. Currently, there's no way for clients to be notified asynchronously when a review finishes; they must either poll the API repeatedly or block waiting for the response. This creates poor UX and wastes server resources. The solution is to implement a webhook system where clients can register callback URLs that receive a POST with the completed review payload. This requires new endpoints in `api/routes/webhooks.py` for webhook management (register/list/delete) and a new service in `core/services/webhook_service.py` to handle registration, delivery, and retry logic with exponential backoff for failed deliveries.

**"Is this right for me?" checklist reasoning:**

- *Understanding:* The issue asks for a webhook system so clients aren't stuck polling or blocking during 30-90 second multi-repo reviews. Success looks like: a client registers a callback URL, kicks off a review, walks away, and receives a POST with the review payload once it's done, with no polling required.
- *Tier fit:* I've contributed to large codebases before, so a Tier 3 issue is a reasonable stretch rather than a first-timer's leap. This issue touches multiple parts of the system (new API route, new service layer, DB model for registrations, and a hook into the existing review-completion path), which matches the Tier 3 description of requiring understanding across modules rather than a localized fix.
- *Codebase readiness:* I've read the review completion flow in `api/routes/reviews.py` and confirmed there's a clear point to trigger webhook delivery once a review finishes. I also looked at an existing test in `tests/unit/` to understand the fixture and mocking patterns I'll follow for the new webhook tests.
- *Scope/time:* Given my other commitments this cycle, I'm confident I can implement the registration endpoint, delivery service (including retry/backoff), the DB migration, and accompanying tests within the Weeks 8-9 window. No open blockers or dependencies are listed on issue #87.

**Branch name:** feat/87-webhook-system

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** [https://github.com/hanielee/pathreview/commit/f2393ef](https://github.com/hanielee/pathreview/commit/f2393ef)

**Reproduction summary:**
Started the app locally (`docker compose up -d` for postgres/redis, `alembic upgrade head`, `uvicorn api.main:app`), registered a test user, created a profile, then created a review via `POST /reviews`. Confirmed the response returns immediately with `status="pending"` while `process_review` (`core/services/review_service.py:82-195`) runs as a FastAPI `BackgroundTask`. Polling `GET /reviews/{id}/status` (`api/routes/reviews.py:139-176`) was the only way to observe the review reach `status="complete"`; server logs confirm the status flip and a `review_processing_completed` log line at both the success commit (`review_service.py:169-174`) and failure commit (`review_service.py:198-202`), but no outbound HTTP call or notification of any kind fires at either point. This confirms issue #87's premise: there is currently no push mechanism, only polling.

**Reproduction steps (for reference):**
1. `docker compose up -d && alembic upgrade head && uvicorn api.main:app --port 8000`
2. `POST /auth/register` → get JWT
3. `POST /profiles` (with `github_username`/`portfolio_url`) → get `profile_id`
4. `POST /reviews` with `{"profile_id": ...}` → returns `{"status": "pending", ...}` immediately
5. `GET /reviews/{review_id}/status` polled repeatedly → eventually returns `{"status": "complete"}`
6. Cross-checked `structlog` output: `review_created` → `review_processing_started` → `review_processing_completed`, with no webhook/notification log or outbound call anywhere in between.

**PLAN.md link:** [PLAN.md](./PLAN.md) (repo root, alongside this JOURNAL.md)

**Walkthrough video (recommended):** Not recorded this cycle.

**Blockers or open questions:**
- Need to confirm whether the `db` session passed into `process_review` as a `BackgroundTask` (same session as the originating request, per `api/routes/reviews.py:43`) safely survives long enough to also handle webhook delivery, or whether delivery needs its own session. See PLAN.md risks section.
- Open question on SSRF handling for user-registered webhook URLs (block private IP ranges? out of scope for MVP?). Plan to raise with mentor before Week 9 implementation.
- `tenacity` is a declared but currently unused dependency; need to confirm the installed version supports the async retry decorator pattern I'm planning around before committing to it in the implementation.