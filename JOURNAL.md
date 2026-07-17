## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists the PathReview HTTP endpoints (health, auth, profiles, and reviews) and points developers to Swagger/ReDoc, but it never shows how to call those endpoints from the terminal. That makes first-time setup harder: after `make run`, there is no copy-paste way to confirm the API is up or to try register/login/profile/review flows without reading OpenAPI interactively. A successful fix adds realistic, copy-pasteable `curl` examples for each documented endpoint (including auth headers and sample JSON bodies where needed) so new contributors can verify the local API quickly against `localhost:8000`.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
