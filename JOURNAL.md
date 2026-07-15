## Week 7 — Issue selection

**Issue link:** 
https://github.com/ascherj/pathreview/issues/87

**Issue title:** 
Implement a webhook system that notifies users when their review is ready.


**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

In the current implementation, a user has a Reviews tab that lets them see the progress of their reviews. However, there isn't a way to notify users when reviews are completed and it is upto the user to check it themselves.

Adding a webhook as a new route helps to setup notifications and notify when each review is processed.

The following are parts of the codebase that requires changes.

    api/routes/ (new webhooks.py)
    core/services/ (new webhook_service.py)

**Branch name:** enhancement/87-webhook-that-notifies-users-when-review-is-ready

**Setup confirmation:** App runs locally at localhost:5173 (with minor changes to point to `127.0.0.1:5173` as `node` resolves localhost to `::1` IPv6 address on macOS)

**Cohort ledger:** [x] Issue added to cohort ledger