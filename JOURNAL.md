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

**Reproduction commit link:** [commit link](https://github.com/BPATHAK10/pathreview/commit/8c6c3c81eabb95aa91dbc1921e5ecd343de6a198)

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

**PLAN.md link:** [plan.md](https://github.com/BPATHAK10/pathreview/blob/test/88-reviews-no-ingested-docs/PLAN.md)

**Blockers or open questions:**
The main open question is the intended contract for an empty profile: should the review still
complete, short-circuit to a distinct status, or simply not error? I want to confirm this with
the maintainers before writing the assertion in Week 9 so I don't codify the current
placeholder behavior if it's unintended.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the test-only fix for issue #88 in `tests/unit/test_review_service.py`. Working
from PLAN.md, I added an `empty_profile` fixture (all four source fields — `github_username`,
`portfolio_url`, `resume_text`, `resume_filename` — set to `None`) and three focused tests:

1. `_run_ingestion_pipeline` returns `[]` for an empty profile and still commits with nothing staged
2. a contrast test showing a profile with a GitHub username yields a non-empty result, so the empty assertion isn't vacuous
3. `process_review` runs the empty-document path
end-to-end without raising and processes the empty profile (rather than rejecting it as "not found"). 

Following the plan's decision to keep assertions contract-neutral while the maintainer contract is unconfirmed, the tests deliberately do not assert the final review status and they pin only the deterministic, defensible behavior.

All three new tests pass. Before my change `tests/unit/test_review_service.py` was 6 passed / 13 failed; after it is 9 passed / 13 failed — the same 13 pre-existing failures, +3 new passing tests, no new failures.

**Next steps:**
Run the full `make check` and `make test-unit` and record pre-existing vs. new failures, open a draft PR, and request peer/mentor feedback in the Slack channel before marking it ready.

**Blockers:**
No any major blockers

---

### Check-in 2 (end of week)

**PR link:** [draft pr](https://github.com/ascherj/pathreview/pull/364)

**Branch:** `test/88-reviews-no-ingested-docs`

**What you built:**
Focused unit tests that pin the "no ingested documents" (empty-profile) review path for
`POST /reviews`, closing the coverage gap in issue #88. The tests assert that ingestion yields
zero sources for an empty profile and that `process_review` handles that empty result without
erroring — deterministic assertions that don't codify the placeholder's fabricated-feedback
behavior. No product code was changed (Tier 1, test-only).

**Tests added or updated:**
`tests/unit/test_review_service.py` — added an `empty_profile` fixture and three tests
(`test_ingestion_pipeline_returns_empty_for_profile_with_no_sources`,
`test_ingestion_pipeline_returns_sources_when_github_present`,
`test_process_review_handles_empty_ingestion_without_error`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Note on "passes": this codebase has documented pre-existing failures. `make test-unit` was 53 failed / 375 passed before my change and 53 failed / 378 passed after (+3 new passing tests, no new failures). My change adds no new `make check` or `make test-unit` failures.

**Draft PR feedback received from:** none

