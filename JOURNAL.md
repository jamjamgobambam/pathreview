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