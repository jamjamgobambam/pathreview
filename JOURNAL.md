# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The review routes have basically no test coverage right now. The file the issue points to, tests/unit/test_review_routes.py, does not even exist in the repo. The closest thing we have is tests/unit/test_review_service.py, and that file only tests create_review, get_review, and list_reviews against a mocked DB session. It never spins up the actual POST /reviews endpoint and never touches process_review, which is the background task that actually runs the ingestion pipeline. So right now nothing proves what happens when someone creates a review for a profile that has no github username, portfolio url, or resume text on file. A fix here means adding a test that hits the endpoint with that kind of empty profile and confirms we get back a sane error instead of a crash or a silent pending review that never resolves.

**Scope/fit reasoning:**
I picked this one as my first issue because it's tagged tier 1 and good first issue, it's unassigned, and I checked issue #88 directly and confirmed it says no pull requests yet. The maintainer estimated 2 to 3 hours for it too. It stays contained to one endpoint and one new test file, so I don't need to fully understand the AI internals fully in depth, just enough to know what should happen when there are no ingested documents. I also noticed a bunch of other tier 1 issues like issue #149 already have open PRs from other students, so that's why I also decided on this one.

**Branch name:** test/88-review-no-ingested-content

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Anthony-Jerez/pathreview/commit/4b19bf2

**Reproduction summary:**
I wrote a test that POSTs to /reviews for a profile with no github username, portfolio url, or resume text, and expects a 422 back. Running it against the current code shows the endpoint always returns 200 instead, which confirms there is no validation anywhere in the request path for a profile with no ingested content.

**Reproduction Steps:**
1. Traced the full review creation flow through api/routes/reviews.py and core/services/review_service.py.
2. Found that create_review_endpoint and create_review never check whether a profile has any ingested content, or even whether the profile exists, before creating the review and scheduling the background processing task.
3. Wrote tests/unit/test_review_routes.py using FastAPI's TestClient, with get_current_user and get_db overridden and the background process_review task mocked out, so the test only exercises the endpoint's own logic.
4. Ran pytest tests/unit/test_review_routes.py -v -m unit and got a failure: the response came back 200 instead of the 422 I asserted, which reproduces the exact gap issue 88 describes.

**PLAN.md link:** https://github.com/Anthony-Jerez/pathreview/blob/test/88-review-no-ingested-content/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Still deciding whether "no ingested content" should be checked off the three profile fields directly or by counting IngestedSource rows for the profile. They're equivalent today but might not stay that way if ingestion changes later. Also haven't checked yet whether the frontend assumes review creation always succeeds, that needs a look before the actual fix goes in during week 9.
