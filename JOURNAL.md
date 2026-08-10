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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- I reviewed the tests/unit/ files to understand the pytest structure. I noticed standard patterns like prefixing names with "test", tagging classes with @pytest.mark.unit, and using @pytest.fixture for reusable setup and mocks.
- I started creating fixtures and getting a better handle on how mocking is implemented while working on test_review_routes.py.

**Next steps:**
- I have to work on finalizing the test file to ensure all edge cases associated with this issue are covered.

**Blockers:**
- I'm still getting used to mocks, fixtures, and syntax.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/673

**Branch:** test/88-review-no-ingested-content

**What you built:**
POST /reviews now looks up the profile before creating anything, using the existing get_profile service. If the profile doesn't exist or isn't owned by the current user it returns 404, and if the profile exists but has no github username, portfolio url, or resume text, it returns 422 with a message explaining why. Only after both checks pass does it go on to create the review and schedule the background processing like before.

**Tests added or updated:**
tests/unit/test_review_routes.py now has three tests instead of the one reproduction test from week 8. One confirms 422 for a profile with no content, one confirms 404 for a profile that doesn't exist, and one is a regression check confirming a profile that does have content still gets back a 200 with status pending.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note on what "passes" means here: this codebase already has pre-existing failures unrelated to my change. make lint has 180 pre-existing errors repo wide (my two files went from 14 to 12 since I cleaned up an unused import and import ordering along the way), make typecheck fails early because of a numpy stub compatibility issue in this environment that happens with or without my change, and make test-unit already had 53 failing tests before I touched anything. I confirmed none of that is new. Before my fix, running the full suite gave 54 failed and 375 passed. After my fix it's 53 failed and 378 passed, so the one test I expected to flip did, two more tests got added, and nothing else changed. Scoped mypy on api/ and core/ with --ignore-missing-imports also stayed at exactly 62 errors before and after.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback yet on [PR #673](https://github.com/ascherj/pathreview/pull/673). It's still open and unreviewed as of this check in.

**How you responded:**


---

### Reflection

**What was harder than you expected?**

Getting onboarded to the codebase was harder than I expected. Before I could even think about the fix, I had to spend real time just reading through api/routes/reviews.py and core/services/review_service.py to understand how a review actually gets created and processed. On top of that I had to make sure I had the right dependencies set up for the project to even run locally, and this was also my first real exposure to pytest, so fixtures, mocks, and the whole testing setup took some getting used to before I felt comfortable writing my own tests.

**What did you learn about working in a large codebase?**

Working in a codebase like this takes a lot more time up front than working on my own project would. I can't just go straight into coding, I have to get familiar with how things are organized and how existing pieces already solve similar problems before I add anything new. That extra time is what keeps me from introducing bugs I didn't mean to, and it also makes sure whatever I write is something another contributor could actually follow and understand later. I saw this play out directly with my own fix. My first plan assumed checking IngestedSource rows would tell me whether a profile had content, but once I got into the actual implementation I realized that check was circular, since those rows only get created after a review already exists. I also ran into a good amount of pre-existing lint, type, and test failures in the repo that had nothing to do with my change, and I had to learn how to tell those apart from anything I introduced myself.

**How did AI tools help — and where did they fall short?**

AI tools were most helpful for understanding the codebase itself, explaining what functions did, walking me through unfamiliar syntax, and pointing me toward where the actual gap in the code was. Once it came to figuring out which edge cases actually mattered to test though, like the missing profile case, the no content case, and making sure the normal case still worked, I wanted to think through those myself instead of letting that get decided for me. That part felt like something I needed to reason through on my own to actually understand the issue.

**What would you do differently if you started over?**

I would spend more time in the planning step before jumping into implementation. My PLAN.md draft going into week 9 assumed the IngestedSource row count was a safe way to check for content, and that only got caught once I was actually writing the fix. If I had sat with the plan a little longer and traced through when those rows actually get created, I probably would have caught that circular logic earlier instead of correcting it mid implementation.

**What are you most proud of from this module?**

I'm most proud of getting to go through something that actually resembles a real open source contribution from start to finish. Picking an issue, reproducing it, writing an actual plan, implementing the fix, and opening a PR for it feels a lot more meaningful than just building something on my own from scratch, since it forced me to work within someone else's codebase and conventions which is something I don't often have the chance to do.