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

**Reproduction commit link:** [https://github.com/hanielee/pathreview/commit/5f0148d](https://github.com/hanielee/pathreview/commit/5f0148d)

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
- The current repo already has unrelated unit-test failures in other modules, so the webhook work was validated with targeted tests and compile checks instead of claiming a full-suite pass.
- SSRF handling for user-provided callback URLs remains a follow-up consideration for a future hardening pass.

## Week 9 - Implementation summary

**Branch:** feat/87-webhook-system

**Implementation summary:**
Implemented a webhook registration and delivery flow for completed or failed reviews. The change adds webhook persistence and delivery-history models, authenticated API endpoints for registering/listing/deleting callbacks, a service that signs outbound POST payloads with HMAC-SHA256 and retries transient failures, and integration into the review completion path so notifications fire on both success and failure.

**Files added/updated:**
- Added [api/routes/webhooks.py](api/routes/webhooks.py) and [api/schemas/webhook.py](api/schemas/webhook.py) for authenticated webhook registration, listing, and deletion endpoints.
- Added [core/models/webhook.py](core/models/webhook.py) and [core/models/webhook_delivery.py](core/models/webhook_delivery.py) plus [alembic/versions/003_add_webhooks.py](alembic/versions/003_add_webhooks.py) to persist webhook registrations and delivery attempts.
- Added [core/services/webhook_service.py](core/services/webhook_service.py) and wired it into [core/services/review_service.py](core/services/review_service.py) so review completion triggers outbound notifications.
- Added targeted tests in [tests/unit/test_webhook_service.py](tests/unit/test_webhook_service.py).

**Tests:**
- `pytest tests/unit/test_webhook_service.py -q` → 6 passed
- `python -m compileall api core tests/unit/test_webhook_service.py` → completed successfully
- `pytest tests/unit -q` still reports unrelated existing failures in other modules, so I did not claim a full-suite pass for this week.

**PR description draft:**
- **Summary:** Added an authenticated webhook system so review completions can notify clients asynchronously instead of requiring polling.
- **Issue:** Closes #87.
- **Changes:** Registered webhook models and migration, added webhook CRUD routes, implemented signed delivery and retry logic, and wired notifications into both success and failure paths for review processing.
- **Testing:** Verified the new behavior with `pytest tests/unit/test_webhook_service.py -q` and a compile check via `python -m compileall api core tests/unit/test_webhook_service.py`.
- **Notes for Reviewers:** The webhook delivery flow records delivery attempts and retries transient failures; no PR or remote push was created while keeping the work local as requested.

**Self-review checkboxes:**
- [ ] `make check` passes
- [ ] `make test-unit` passes

**Check-in 1 (mid-week)**

**Current progress:**
Implemented the webhook data model, migration, API routes, delivery service, and review-flow integration for issue #87. The core webhook registration/list/delete flow and signed delivery/retry logic are now in place, and the webhook-specific unit tests are passing locally.

**Next steps:**
Finalize the Week 9 journal check-ins, confirm the branch state, and prepare the PR description and review notes for submission.

**Blockers:**
No blockers at this stage; only the broader repo still has unrelated existing unit-test failures outside the webhook scope.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/1026](https://github.com/ascherj/pathreview/pull/1026)

**Branch:** `feat/87-webhook-system`

**What you built:**
Added an authenticated webhook system so completed or failed reviews can notify clients asynchronously with signed POST payloads and retry handling, instead of relying only on polling. The implementation includes webhook registration endpoints, persistence for webhook registrations and delivery attempts, and integration into the review completion flow.

**Tests added or updated:**
- Added [tests/unit/test_webhook_service.py](tests/unit/test_webhook_service.py) covering registration, listing, deletion, successful delivery, retry-then-success, and failed-after-retries.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note: the webhook-specific tests pass locally, but the broader repository still shows unrelated pre-existing failures in other modules, so I did not mark the full-suite checks as passing.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback had arrived by the end of the module, so I documented that the PR was still awaiting review and moved forward with the final reflection and branch submission.

**How you responded:**
No direct response was needed. I kept the implementation and journal updated, and I left the branch in a state that was ready for review once feedback began arriving.

---

### Reflection

**What was harder than you expected?**
The hardest part was not writing the webhook feature itself, but understanding how the review flow fit together across multiple layers of the app. I had to trace the path from the review API route into the background processing service and then into the new webhook delivery logic, and that required more careful debugging than I expected because the repository already had unrelated test issues that made it harder to tell whether a failure was caused by my changes or by existing noise.

**What did you learn about working in a large codebase?**
I learned that contributing to someone else’s production code is less about implementing a feature in isolation and more about fitting your change into an existing architecture without breaking assumptions elsewhere. In this project, the webhook work touched the API layer, service layer, database model layer, and tests, and that reinforced how important it is to understand the surrounding patterns before making changes that seem small at first.

**How did AI tools help — and where did they fall short?**
AI tools were especially helpful for speeding up the initial implementation plan, generating test ideas, and helping me reason through the webhook service structure when I was still mapping the project. They were less useful when it came to the more subtle parts of the work, such as diagnosing why existing unit tests were failing in other modules and making sure the change matched the project’s style and conventions rather than just producing plausible code.

**What would you do differently if you started over?**
If I started over, I would spend more time earlier on mapping the relevant files and the existing review lifecycle so I could plan the implementation more precisely from the beginning. I would also try to isolate the repo’s pre-existing test failures sooner, because that would have made the validation process less confusing and given me a clearer signal about which issues were truly caused by the webhook work.

**What are you most proud of from this module?**
I’m most proud of finishing a cross-cutting feature that connected several parts of the system, from the API routes to the persistence layer and the review completion path. Seeing the webhook flow become real in the codebase, even while working around unrelated project issues, felt like a meaningful milestone in my growth as a contributor.