# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/88

**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There is no route-level test coverage anywhere in the API — not just for this
endpoint, but for any endpoint in the app. `POST /reviews` accepts a profile_id
and immediately returns a pending review with no check that the profile actually
has any ingested content (GitHub username, portfolio URL, or resume). The
background task that's supposed to process the review is currently built from
placeholder logic, so a profile with zero ingested sources doesn't error out —
it silently produces a fake "complete" review with fabricated content and a
canned score. A successful fix adds an upfront validation check that rejects
profiles with no ingested content, and a new test file (the first route-level
test file in the repo) verifying that behavior.

**Scope reasoning:**

*Part 1 — Understanding the issue*
- [x] Explained in my own words: `POST /reviews` never checks whether a profile
  has any ingested content (GitHub username, portfolio, or resume) before
  creating a review. Because the background processing step is currently
  placeholder logic, a profile with nothing ingested doesn't get an error back
  — it silently receives a fake "complete" review with fabricated content and
  a canned score. The fix should reject that case with a clear error and add a
  test proving it.
- [x] Affected area confirmed: `api/routes/reviews.py` (the endpoint) and
  `core/services/review_service.py` (`create_review`, `process_review`) — both
  read in full. The issue's own labels (`api`, `tests`, `docs`, `devops`)
  confirm this is an API-layer issue, not ingestion or frontend.
- [x] Concrete before/after: **Before** — POST a profile with no ingested
  sources, get a 200 and, eventually, a fabricated "complete" review with
  made-up sections. **After** — the same request returns a clear 4xx error
  immediately, with a test asserting that behavior.

*Part 2 — Tier fit*
- [x] Tier 1 — matches the issue's own `tier-1` label, and this is my first
  open-source contribution, so I'm not reaching for Tier 2/3 yet.

*Part 3 — Codebase readiness*
- [x] Read the specific code the issue references: `api/routes/reviews.py:22-62`
  (`create_review_endpoint`) and all of `core/services/review_service.py`,
  including the placeholder `_run_ingestion_pipeline` /
  `_run_agent_orchestration` / `_run_rag_retrieval_generation` steps that
  `process_review` calls.
- [x] Understand it well enough to sketch a fix: add a check in
  `create_review_endpoint` (or the `create_review` service function) that
  rejects a profile with no ingested content via a 422, before a `Review` row
  is even created.
- [x] Read the relevant test file end-to-end: there's no existing route-level
  test file for this endpoint — that's the gap itself. Read
  `tests/unit/test_review_service.py` end-to-end instead, since it's the
  closest existing pattern: it mocks the DB session directly with
  `AsyncMock`/`Mock` and never goes through FastAPI's `TestClient` or the HTTP
  layer. This confirms the new test file will be the first one in the repo
  that tests through the actual route/HTTP layer, not just the service
  function directly.

*Part 4 — Scope and time*
- [x] Not already claimed: verified zero comments before commenting, then
  confirmed via the GitHub API that mine is the only comment.
- [x] Realistic for Weeks 8–9: issue estimate is 2–5 hours, Tier 1, comfortably
  within the two-week window.
- [x] No blockers: read the full issue body — no "blocked by" reference to any
  other issue.

**Branch name:** test/88-review-no-ingested-documents

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/OmJam/pathreview/commit/f3af37a8c45707cd3edc0617bde951a1d321b752

**Reproduction summary:**
Reproduced two ways. Live: registered a throwaway user, created a profile
with no github_username/portfolio_url/resume, and POSTed a review for it —
it reached `status: "complete"` on the very first poll, with three fully
fabricated feedback sections ("Technical Skills", "Project Experience",
"Career Growth") and `overall_score: 0.81`, and `error_message: null`,
despite the profile having zero real content. Code-level: added
`test_no_ingested_content_should_not_produce_fabricated_review` to
`tests/unit/test_review_service.py`, which calls the same placeholder
pipeline functions (`_run_agent_orchestration`, `_run_rag_retrieval_generation`,
`_run_safety_checks`) directly with an empty-content profile and asserts they
shouldn't produce a safety-check-passing, fully-sectioned result from
nothing — confirmed failing via `.venv/bin/pytest tests/unit/test_review_service.py -v`.

**PLAN.md link:** https://github.com/OmJam/pathreview/blob/test/88-review-no-ingested-documents/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Resolved during Week 9 implementation — the fix ended up in both the route
layer and `process_review` (defense-in-depth), and the `error_message` gap
on the two pre-existing failure paths was deliberately left alone to keep
the PR scoped to #88 (documented in PLAN.md and the PR description).

## Week 9 — Solution building & PR submission

### Check-in

**PR link:** https://github.com/ascherj/pathreview/pull/325

**Branch:** test/88-review-no-ingested-documents

**What you built:**
`POST /reviews` now loads the profile before creating a review and returns
404 (not found/not owned) or 422 ("Profile has no ingested content to
review") instead of silently completing with fabricated feedback.
`process_review` runs the same check as a defense-in-depth guard, and is
the first code path in the app to ever populate the `error_message` column
on failure.

**Tests added or updated:**
Rewrote the Week 8 reproduction test in `tests/unit/test_review_service.py`
to assert the fixed behavior (fails on pre-fix code, passes now — verified
both ways via `git stash`). Added `tests/unit/test_review_routes.py` — the
first route/HTTP-layer tests in the repo, covering 404, 422 for empty and
whitespace-only profiles, and the happy-path regression — and
`tests/unit/test_profile_service.py` (8 parametrized cases for the new
`profile_has_ingested_content` helper).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(documented pre-existing failures: 53 unit-test failures across 11 files
and 103 mypy errors across 26 files predate this branch; confirmed via
`git stash` baseline diffing that this PR introduces zero new failures in
either — see PLAN.md "Status" and the PR's "Pre-existing issues" section)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
Checked PR #325 on 2026-08-03 via `gh pr view 325 --json
comments,reviews,reviewRequests`: 0 comments, 0 reviews, 0 review requests
since it opened on 2026-07-27. No maintainer or reviewer feedback arrived.
Per this term's course note, reviewer feedback isn't provided in Su26, so
this is the expected outcome rather than a stalled review.

**How you responded:**
*(No feedback arrived, so no response was needed — no changes made to the PR
this week.)*

---

### Reflection

**What was harder than you expected?**
Keeping a running mental model of the whole system was harder than I
expected — not just the one endpoint I was fixing, but how
`api/routes/reviews.py`, `core/services/review_service.py`, and
`core/services/profile_service.py` all handed data to each other, and where
the placeholder pipeline stages (`_run_agent_orchestration`,
`_run_rag_retrieval_generation`, `_run_safety_checks`) sat in that flow.
Every time I came back to this after a few days between Weeks 7–9, I had to
re-derive where I'd left off and why. The harder problem underneath that was
knowing when testing was "enough": it was easy to keep finding more cases
(whitespace-only fields, a profile edited after creation to remove its only
content, the two pre-existing `process_review` failure paths that still
don't set `error_message`), and I had to consciously draw a line — cover
what #88 actually asked for, and write the rest into `PLAN.md` as
explicitly out of scope instead of chasing it all into one PR.

**What did you learn about working in a large codebase?**
Most of the actual time went into understanding, not writing. Before I
changed a line, I had to read `create_review_endpoint` end-to-end and trace
`process_review`'s four placeholder stages to see that the real bug wasn't
"missing one validation" so much as "nothing in the pipeline ever checks its
own input." In my own projects I'd just know that already. Here, correctness
alone wasn't the bar, either — matching `docs/CONTRIBUTING.md`'s branch
naming, Conventional Commits format, and the PR template mattered almost as
much as the fix, since a maintainer reviewing many PRs is relying on that
consistency to move fast. I also learned to verify against a baseline
instead of a fresh run: `make test-unit` and `make typecheck` both had
pre-existing failures (54 and 103) unrelated to my change, so "my tests
pass" wasn't good enough — I had to `git stash` and diff before/after to
prove I added zero new failures, a habit I didn't need in solo projects
with no pre-existing debt to separate from.

**How did AI tools help — and where did they fall short?**
AI was most useful as a reading accelerant — pointed at the issue, it helped
me trace `create_review_endpoint` into `process_review`'s placeholder
stages faster than I'd have managed alone, and it was good at narrowing
"which files actually matter for this issue" in a repo I'd never seen
before. It fell short on codebase-specific standards: this repo has
`docs/CONTRIBUTING.md` and a `.github/PULL_REQUEST_TEMPLATE.md` that already
spell out the exact branch-naming scheme, commit format and scopes, and
required PR sections, but AI didn't go find and apply those on its own — I
had to read them myself and feed the rules back in before my branch name,
commits, and PR body actually matched what the repo expects. It also
couldn't tell me when a fix was "enough" — the scoping calls (leaving the
two pre-existing `error_message` gaps alone, treating a syntactically-valid
but fake `github_username` as out of scope) were judgment calls I had to
make and then document myself, not something I could offload.

**What would you do differently if you started over?**
I'd read `docs/CONTRIBUTING.md` and the PR template in full on day one
instead of picking up pieces of them mid-task — the standards were already
written down, I just hadn't consumed them before I started, so I ended up
correcting branch/commit/PR formatting after the fact instead of getting it
right the first time. I'd also spend more of Week 7 mapping how
`reviews.py`, `review_service.py`, and `profile_service.py` actually pass
data to each other — a quick sketch of the request → endpoint → background
task → placeholder-stage flow would have surfaced the "nothing checks its
own input" root cause faster than reading files one at a time as I got to
them.

**What are you most proud of from this module?**
Taking this from "reviews complete with fabricated content and nobody
notices" (the Week 8 reproduction: a zero-field profile reaching
`status: complete` with three made-up sections and a 0.81 score) to a
verified fix with a paper trail — a 422/404 check in the route, a
defense-in-depth copy in `process_review`, tests proving both the bug and
the fix, and a baseline diff showing I didn't break anything else along the
way. What I'm proud of isn't the diff itself, it's that I can explain every
line of it and back it up with evidence I generated myself. That's also the
module's biggest lesson about AI: it clearly sped up understanding an
unfamiliar codebase and drafting the fix, but the parts that made this a
real contribution — deciding scope, verifying against a baseline instead of
trusting a green checkmark, catching that AI's first-pass formatting didn't
match the repo's conventions — only happened because I treated it as a pair
programmer to question and check, not an authority to defer to.
