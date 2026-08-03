# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/89

**Issue title:** API reference doc is missing the `POST /profiles` request body schema

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The API reference file, `docs/API.md`, lists the `POST /profiles` endpoint but
only gives it a one-line description. It never explains what you have to send in
the request, so anyone calling the API has to read the source code or open the
Swagger page to figure it out. The missing detail matters here because this
endpoint is not a normal JSON request — it takes a multipart form with three
optional fields: a GitHub username, a portfolio URL, and a resume file upload
(which must be a PDF or Markdown/plain-text file). A successful fix adds a clear
request body section for this endpoint — a table of the fields with their types
and rules, plus a short example request — so the doc on its own is enough to call
the endpoint correctly. The change only touches the documentation in `docs/API.md`
and does not change how the application behaves.

**Branch name:** docs/89-post-profiles-request-body

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction and plan

**Issue:** #89 — API reference doc is missing the `POST /profiles` request body schema
(https://github.com/ascherj/pathreview/issues/89)

**Walkthrough video:** https://www.loom.com/share/a59ceea3be4d433d99066c6a4cdd3843

**What I did this week:** reproduced the problem on my own machine, then wrote a
structured plan for the fix in `PLAN.md`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`. Completed sub-tasks 1–4: added a request body
section for `POST /profiles` to `docs/API.md` — a `multipart/form-data` + Bearer
auth note, a field table (`github_username`, `portfolio_url`, `resume_file` with
types, length limits, and allowed file types), the resume file-type rule with its
exact `422` message, and a runnable `curl` example. Also added a doc-regression
unit test at `tests/unit/test_api_docs.py` (7 tests, all passing) that guards the
documented schema. Committed the doc fix and the test separately.

**Next steps:**
Do the final `make check` / `make test-unit` verification, fill in the PR template,
and open the pull request into `ascherj/main`, then record the link in Check-in 2.

**Blockers:**
None. Note: the repo has pre-existing `make check` (182 ruff errors) and
`make test-unit` (53 failing tests) issues unrelated to this change — I recorded the
baseline first and confirmed my change adds none. This will be documented in the PR.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/659

**Branch:** `docs/89-post-profiles-request-body`

**What you built:**
A request body section for `POST /profiles` in `docs/API.md`. It documents that the
endpoint takes a `multipart/form-data` upload with three optional fields
(`github_username`, `portfolio_url`, `resume_file`), their length limits and accepted
resume file types, the required Bearer token (`401` if missing), the `422` returned for
an invalid file type, and a runnable `curl` example — so the doc alone is enough to call
the endpoint correctly.

**Tests added or updated:**
Added `tests/unit/test_api_docs.py` — 7 unit tests that read `docs/API.md` and assert it
documents the `multipart/form-data` content type, all three request fields, the
Bearer-auth/`401` requirement, the accepted resume MIME types (including `text/plain`),
the exact `422` detail message, and a `curl` example. This guards the #89 fix so the
schema can't silently disappear again.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(In this repo "passes" means *no new failures*: my changed files are ruff/black/mypy
clean and my 7 new tests pass; the pre-existing 182 ruff / 5 mypy / 53 test failures are
documented in the PR and unchanged by this PR.)

**Draft PR feedback received from:** none (opened ready for review)
