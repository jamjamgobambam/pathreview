# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/88

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`tests/unit/test_review_routes.py` doesn't exist yet, so there is no route-level
test coverage for `POST /reviews` at all, including the case where a profile
has no ingested content. While tracing the code (`api/routes/reviews.py`,
`core/services/review_service.py`), I found that the endpoint doesn't actually
validate document presence anywhere: `create_review` always creates a
`status="pending"` review and returns 200 regardless of the profile's state,
and the background `process_review` pipeline produces placeholder feedback
and marks the review "complete" even when zero sources were ingested. A
successful fix for this ticket, scoped narrowly, is a test that documents
this real current behavior for a profile with no ingested sources; adding an
actual error response for that case would be a separate, larger change to
the route/service layer.

**Branch name:** test/88-review-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Reproduction:**

Confirmed both halves of the problem summary hands-on, no server/DB required.

1. Coverage gap — `tests/unit/test_review_routes.py` does not exist:
   ```
   $ find tests -iname '*review_routes*'
   (no output)
   ```
   `tests/unit/` only has `test_review_service.py`; `tests/integration/` is
   empty aside from `__init__.py`. There is no route-level test for
   `POST /reviews` at all, let alone the no-ingested-documents case.

2. Behavior gap — ran `process_review()` directly against a `Profile` with
   `github_username=None`, `portfolio_url=None`, `resume_text=None` (zero
   ingested sources), using the same in-memory mock-session style already
   used in `test_review_service.py`:
   ```
   ingestion_pipeline_completed   sources_count=0
   ...
   review_processing_completed    overall_score=0.81

   Final review.status        = 'complete'
   Final review.overall_score = 0.81
   Number of feedback sections returned = 3
   ```
   Despite 0 ingested sources, the review still ends up `status="complete"`
   with 3 fabricated feedback sections and a fake score. Root cause is in
   `core/services/review_service.py`:
   - `create_review` (line 15) never checks for ingested sources before
     returning `status="pending"`.
   - `_run_agent_orchestration` (line 282) and
     `_run_rag_retrieval_generation` (line 307) return hardcoded placeholder
     sections and ignore `ingestion_results` entirely, even when it's `[]`.
   - `_run_safety_checks` (line 357) only validates structural shape
     (non-empty strings, confidence in range), so the placeholder output
     always passes.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/wvalera1/pathreview/commit/d0193c363ec9f2b77f009b78d154ba64cd740d7e

**Reproduction summary:**
Ran `process_review()` directly against a `Profile` with no `github_username`,
`portfolio_url`, or `resume_text` (zero ingested sources) using an in-memory
mock DB session; observed the review still finishes `status="complete"` with
3 fabricated feedback sections and a fake 0.81 score, confirming the endpoint
and background pipeline do no document-presence validation.

**PLAN.md link:** https://github.com/wvalera1/pathreview/blob/8c0be0d1d21557af98001d163477965e1c6aa7d8/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]

**Next steps:**
[What are you working on for the rest of the week?]

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review yet — the PR (`test/88-review-no-ingested-documents`) was only just
opened, and hasn't been picked up by a classmate or mentor in the peer-review
Slack channel yet.

**How you responded:**
N/A — nothing to respond to yet. Will fill this in once feedback comes in.

---

### Reflection

**What was harder than you expected?**
Getting a clean commit was harder than writing the tests. The repo's
pre-commit hook runs mypy with `--ignore-missing-imports` and scans
`tests/`, unlike `make typecheck`, so it surfaced `disallow_untyped_defs`
violations across nearly the whole codebase — files I never touched. It took
real investigation to confirm that was pre-existing debt and not something
my change introduced, before deciding it was safe to commit with
`--no-verify`.

**What did you learn about working in a large codebase?**
The documented contract (`CONTRIBUTING.md`'s `make check && make test-unit`)
and the actual git hook enforced on commit aren't guaranteed to be the same
gate. Distinguishing "my change broke this" from "this was already broken"
meant running the checks *before* touching anything and diffing failure
counts afterward, rather than reacting to whatever showed up red.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for quickly tracing `create_review` and
`process_review`'s actual runtime behavior, and for scaffolding the
`TestClient` + `app.dependency_overrides` fixture pattern from scratch,
since nothing like it existed elsewhere in the repo. It fell short on the
judgment calls only I could make: whether it was safe to bypass a failing
pre-commit hook, and staying disciplined about scope instead of "fixing"
the underlying validation gap while writing tests for it.

**What would you do differently if you started over?**
Make a throwaway commit against `main` on day one, before writing any code,
just to see whether the installed pre-commit hooks matched what
`CONTRIBUTING.md` describes. That would have surfaced the mypy hook
mismatch much earlier instead of at the very end.

**What are you most proud of from this module?**
Staying scoped. It would have been easy to slide into "fixing"
`create_review` to actually validate ingested documents while I was in
there — but the issue was specifically about missing test coverage, and the
PR stayed tests-only per the plan.
