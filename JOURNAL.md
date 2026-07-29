## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/117

**Issue title:** API docs don't include example `curl` commands

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`docs/API.md` lists the PathReview HTTP endpoints (health, auth, profiles, and reviews) and points developers to Swagger/ReDoc, but it never shows how to call those endpoints from the terminal. That makes first-time setup harder: after `make run`, there is no copy-paste way to confirm the API is up or to try register/login/profile/review flows without reading OpenAPI interactively. A successful fix adds realistic, copy-pasteable `curl` examples for each documented endpoint (including auth headers and sample JSON bodies where needed) so new contributors can verify the local API quickly against `localhost:8000`.

**Branch name:** docs/117-api-curl-examples

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the documentation plan for issue #117. The API reference now includes
copy-pasteable `curl` commands for authentication, profile management, review
creation and polling, pagination, and cleanup.

**Next steps:**
Validate the commands against the current route contracts, run the project
checks, request draft-PR feedback, and finalize the submission.

**Blockers:**
The repository has pre-existing `make check` and `make test-unit` failures;
the documentation-only change does not modify the affected code.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/354

**Branch:** `docs/117-api-curl-examples`

**What you built:**
Expanded `docs/API.md` into an executable API reference for issue #117. It
documents setup, token and ID capture, request formats, authenticated calls,
asynchronous review polling, pagination, and final cleanup for every public
API route.

**Tests added or updated:**
No application code changed. I verified every documented route and request
format against the current FastAPI route definitions and parsed all Bash code
blocks with `zsh -n`.

**Self-review confirmation:** [x] `make check` introduces no new failures  [x] `make test-unit` introduces no new failures

`make check` has 35 existing lint/type errors and `make test-unit` has 89
existing test errors, all in files outside this documentation-only change.

**Draft PR feedback received from:** none
