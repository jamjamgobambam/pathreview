## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/87](https://github.com/ascherj/pathreview/issues/87)

**Issue title:** Implement a webhook system that notifies users when their review is ready #87

**Tier:** [ ] Tier 1  [ ] Tier 2  [X] Tier 3

**Problem summary:**
When users request AI reviews of multiple repositories, the process takes 30–90 seconds to complete. Currently, there's no way for clients to be notified asynchronously when a review finishes—they must either poll the API repeatedly or block waiting for the response. This creates poor UX and wastes server resources. The solution is to implement a webhook system where clients can register callback URLs that receive a POST with the completed review payload. This requires new endpoints in `api/routes/webhooks.py` for webhook management (register/list/delete) and a new service in `core/services/webhook_service.py` to handle registration, delivery, and retry logic with exponential backoff for failed deliveries.

**Branch name:** feat/87-webhook-system

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger