## Week 7 — Issue selection

**Issue link:** 
https://github.com/ascherj/pathreview/issues/87

**Issue title:** 
Implement a webhook system that notifies users when their review is ready.


**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Selection reasoning**

Using the ***Is this right for me?*** checklist, I chose this issue:

Part 1 — Understanding the Issue

Details are in problem summary below.

Part 2 — Tier Fit

1. Prior experience with open source contributions, hence seeked a Tier 3 issue to work on.
2. Webhook systems are examples of asynchronous workflows, which are usually harder to implement reliably and test, making it a good exercise with my experience as a software engineer.

Part 3 — Codebase Readiness

The Problem Summary below describes the files that needs the changes. Since this is a new service, a new test file should be setup.

Part 4 — Scope and Time

Issue states that it will take 8-12 hours. Allowing buffer time for issues coming up, it will take around 12-15 hours to setup a new webhook, write new unit and integration tests and update the frontend if needed. A week is enough for me to complete these, especially since I will be using Claude Code to help me write the code and tests based on the implementation plan that I will draft.

**Problem summary:**

In the current implementation, a user has a Reviews tab that lets them see the progress of their reviews. However, there isn't a way to notify users when reviews are completed and it is upto the user to check it themselves.

Adding a webhook as a new route helps to setup notifications and notify when each review is processed.

The following are parts of the codebase that requires changes.

    api/routes/ (new webhooks.py)
    core/services/ (new webhook_service.py)

**Branch name:** enhancement/87-webhook-that-notifies-users-when-review-is-ready

**Setup confirmation:** App runs locally at localhost:5173 (with minor changes to point to `127.0.0.1:5173` as `node` resolves localhost to `::1` IPv6 address on macOS)

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
This issue is a new feature rather than a bug so skipping this section.

**Reproduction summary:**
This issue is a new feature rather than a bug so skipping this section.

**PLAN.md link:** 
[PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**
<NA>

**Blockers or open questions:**
<NA>

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All implementation is completed, including testing and documentation.

**Next steps:**
Setting up the PR, its documentation before submission. 
Also submit the PR for review once done.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/708

**Branch:** `feat/87-webhook-that-notifies-users-when review-is-ready`

**What you built:**
A webhook notification system for completed reviews: clients register a callback URL per profile via `POST /webhooks/callbacks`, and once a review finishes processing, PathReview POSTs a `review.completed` notification (with a deterministic `notification_id` and up to 3 retries) to that URL.

**Tests added or updated:**
Added`tests/unit/test_webhook_service.py` and `tests/unit/test_callback.py` (20 tests total).
Updated `tests/unit/test_review_service.py`(2 tests total).
Covers callback registration/deletion (success, already-registered `409`, profile-not-owned `404`), notification creation and dedup by `notification_id`, and `send_notification`'s success/retry/max-attempts/timeout paths — asserting the exact POST payload and retry counts, not just end state, notification delivery when callback exists, no delivery when callback doesn't exist.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** None, raised PR.

### PR Description

## Summary

In the current implementation, a user has a Reviews tab that lets them see the progress of their reviews. However, there isn't a way to notify users when reviews are completed, and it is up to the user to check it themselves. Adding a webhook as a new route helps to set up notifications and notify when each review is processed.

## Issue

Closes #87

## Changes

- Added `Callback` and `Notification` models and the corresponding migration.
- Added `webhook_service.py` with registration/removal + delivery (3 retries, 5s timeout per attempt).
- Added `POST /webhooks/callbacks` and `DELETE /webhooks/callbacks/{profile_id}` routes and schemas.
- Updated `process_review` in `review_service.py` to call `notify_callback_on_review_completed` as a separate task, so notifications are sent without blocking `process_review`.
- Added a runnable example client with dedup, plus a setup walkthrough, and updated [docs/API.md](docs/API.md) with a new `### Webhooks` section and example link.
- Added missing type packages to the pre-commit `mypy` hook so it checks against real types (see [Notes for Reviewers](#notes-for-reviewers)).
- Fixed a `B008` lint issue during the pre-commit hook (see [[Notes for Reviewers](https://claude.ai/chat/66897adc-74e8-455a-b24d-2aeeb1908aaf#notes-for-reviewers)](#notes-for-reviewers)).

## Testing

- **Unit tests** (`tests/unit/test_webhook_service.py`, `tests/unit/test_callback.py`, 20 total) cover:
  - Registering/deleting a callback (success, already-exists `409`, profile-not-owned `404`).
  - Notification create/dedup by `notification_id`.
  - `send_notification`'s success/retry/max-attempts/timeout paths.

These mock `httpx.AsyncClient` to assert the exact POST payload and retry/attempt counts, rather than just the end state.

- **Manual end-to-end run** (more details in [docs/examples/client_callback_setup.md](docs/examples/client_callback_setup.md)) against a live server (Postgres/Redis via `docker compose`, API on `:8000`, example client on `:9000`):
  1. Logged in.
  2. Registered a callback for a seeded profile.
  3. Requested a review.
  4. Confirmed the client's `/callback` received the notification and logged it.
  5. Confirmed `delivery_status` flipped to `success` in the DB.
  6. Unregistered the callback and confirmed the row was deleted.

**Checklist**

- [x] Unit tests pass (`make test-unit`)
- [ ] Integration tests pass (`make test-integration`)
- [x] Linter passes (`make lint`)
- [x] Type checker passes (`make typecheck`)
- [x] New/updated tests cover the changes

## Screenshots / Demo

N/A — changes are only on the backend, so no screenshots/demo needed. Step-by-step instructions to test the client callback are mentioned in [##Testing](Testing)

## Notes for Reviewers

- Integration tests are not set up in the project as of now, hence skipping integration test checks.
- Added missing type packages to the `mypy` hook in `pre-commit-config.yaml`; otherwise the pre-commit hook fails for successful tests.
- **Lint errors:** ~202 errors repo-wide before the change, mostly:
  - `B904` — `raise` inside `except` without `from err` / `from None`
  - `B008` — do not perform function call `Depends` in argument defaults; instead, perform the call within the function, or read the default from a module-level singleton variable, due to FastAPI's `Depends()`

  Fix made for `B008`(scoped for my changes) to pass the pre-commit hook — in `api/routes/webhooks.py`, added the following to `pyproject.toml`:

  ```toml
  [tool.ruff.lint.flake8-bugbear]
  extend-immutable-calls = ["fastapi.Depends"]
  ```

  This prevents ruff checks from flagging the issue related to [using calls for default arguments](https://docs.astral.sh/ruff/settings/#lint_flake8-boolean-trap_extend-allowed-calls). This change is project-wide, so I've tested it to confirm it doesn't break anything else.

- **Typing errors:** 114 errors repo-wide before the change. Made the following fixes (scoped to my changes) to pass the pre-commit hook:
  - `core/services/webhook_service.py`, `tests/unit/test_review_service.py` — added `db: AsyncSession` typing to 4 functions; annotated `notification: Notification | None` to fix `Returning Any`.
  - `tests/unit/test_callback.py` — fully annotated every fixture/test.
  - `docs/examples/client_callback_server.py` — annotated `data: dict[str, Any] = response.json()` to fix `Returning Any`.
  - `tests/unit/test_webhook_service.py` — fully annotated every fixture/test.
  - `api/routes/webhooks.py` — added `db: AsyncSession`, `-> CallbackResponse` / `-> None` return types; fixed `current_user.id` (`str`) → `UUID(current_user.id)` at both call sites.
  - `core/services/review_service.py` — added `db: AsyncSession` typing to 4 functions; annotated `notification: Notification | None` to fix `Returning Any`.
  - `tests/unit/test_review_service.py` — fully annotated every fixture/test.

