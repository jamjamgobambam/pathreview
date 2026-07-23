# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `POST /reviews` endpoint (in `api/routes/reviews.py`) lets a user kick off a
review for one of their profiles. It creates a review row with `status="pending"`,
returns immediately, and does the heavy lifting in a background task (`process_review` in `core/services/review_service.py`). One realistic situation is a profile that has no ingested documents at all i.e. no GitHub username, portfolio URL, or uploaded resume. This makes the ingestion step produce an empty result set. Right now nothing pins down how the endpoint should behave in that case: the only review tests live in `tests/unit/test_review_service.py`, and there is no test for the empty-profile path, so a future change could silently break it. A successful fix adds a focused test that submits a review for a profile with zero ingested documents and asserts the endpoint's contract (that it still responds as designed rather than erroring on empty input), closing the coverage gap.

**Branch name:** test/88-reviews-no-ingested-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" checklist reasoning:**
This fits my scope as a first contribution for a few reasons. It is test-only work in which I add a test rather than change product behavior, so the blast radius is small and I am unlikely to break existing features. I was able to locate the relevant code
quickly: the handler in `api/routes/reviews.py`, the background logic in
`core/services/review_service.py`, and the existing tests in
`tests/unit/test_review_service.py`, which gives me a pattern to follow. I understand
what "no ingested documents" means in the data model (a profile with no GitHub
username, portfolio URL, or resume, so no `IngestedSource` rows), which is the exact
condition the new test needs to set up. The main thing I need to confirm is the
endpoint's intended behavior in that case so my assertion matches the design rather
than the current implementation.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** REPRO_COMMIT_URL_PLACEHOLDER

**Reproduction summary:**
I reproduced the empty-profile path by driving `core/services/review_service.py` directly
against a profile with no ingested documents (`github_username=None`, `portfolio_url=None`,
`resume_text=None`) using mocked async DB calls, mirroring the fixtures in
`tests/unit/test_review_service.py`. Observed: `_run_ingestion_pipeline` returns `[]` (zero
sources) as expected, but the downstream placeholder steps ignore that empty result — so
`process_review` still marks the review `complete` with 3 fabricated sections and
`overall_score=0.81`, and `_run_safety_checks` passes it. I confirmed no existing test covers
this path (the review tests only touch `create_review`, `get_review`, and `list_reviews`),
so the empty-document contract is entirely unpinned. Reproduction steps:

1. `git checkout test/88-reviews-no-ingested-docs`
2. Build a `Profile` mock with all three source fields set to `None`.
3. Call `_run_ingestion_pipeline(db, profile)` → returns `[]`.
4. Call `_run_agent_orchestration` / `_run_rag_retrieval_generation` / `_run_safety_checks`
   with that empty result → 3 sections, score 0.81, safety passes.
5. Conclusion: the empty-input path is untested and silently produces feedback from zero data.

**PLAN.md link:** https://github.com/BPATHAK10/pathreview/blob/test/88-reviews-no-ingested-docs/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
The main open question is the intended contract for an empty profile: should the review still
complete, short-circuit to a distinct status, or simply not error? I want to confirm this with
the maintainers before writing the assertion in Week 9 so I don't codify the current
placeholder behavior if it's unintended. Secondary: 13 of 19 existing tests in
`tests/unit/test_review_service.py` fail locally due to an `AsyncMock`/asyncio-mode setup
issue unrelated to this issue — I'll model my new test on one of the passing tests.