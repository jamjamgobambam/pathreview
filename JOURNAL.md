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

**PR link:** https://github.com/ascherj/pathreview/pull/405

**Branch:** `Enhancement/87 webhook that notifies users when review is ready`

**What you built:**
A webhook notification system for completed reviews: clients register a callback URL per profile via `POST /webhooks/callbacks`, and once a review finishes processing, PathReview POSTs a `review.completed` notification (with a deterministic `notification_id` and up to 3 retries) to that URL.

**Tests added or updated:**
Added`tests/unit/test_webhook_service.py` and `tests/unit/test_callback.py` (20 tests total).
Updated `tests/unit/test_review_service.py`(2 tests total).
Covers callback registration/deletion (success, already-registered `409`, profile-not-owned `404`), notification creation and dedup by `notification_id`, and `send_notification`'s success/retry/max-attempts/timeout paths — asserting the exact POST payload and retry counts, not just end state, notification delivery when callback exists, no delivery when callback doesn't exist.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

