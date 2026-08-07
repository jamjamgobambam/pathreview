## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [*] Tier 2  [ ] Tier 3

**Problem summary:**
The ingestion pipeline re-embeds every resume, README, and repo submission from scratch on every ingestion call, even when the content is byte-for-byte identical to something already processed. The dedup logic already existed in shape — a content hash was computed and folded into `source_id`, and the `IngestedSource` model even had an unused `content_hash` column — but the wiring was never finished: the skip-check queried a placeholder instead of the real database model and always returned nothing, and the record-keeping step only logged instead of writing to the database. On top of that, the database session is async-only but the pipeline's methods were synchronous, so even a corrected query couldn't have worked as written. A successful fix detects when resubmitted content is unchanged and skips parsing, chunking, and embedding entirely, cutting unnecessary embedding-API calls and redundant vector-store writes without touching the case where content actually changed.

**"Is this right for me?" checklist reasoning:**
I wasn't able to retrieve the course page's own "Is this right for me?" checklist (behind course-portal auth), so this is my scope reasoning based on what's actually verifiable about the issue:
- **Tier fit:** Manifest labels this tier-2 with an estimated 4–6 hours. Reasonable for a fix that touches a well-scoped, single-pipeline concern rather than a cross-cutting or architectural change.
- **Files touched matched the estimate at first glance:** the manifest listed `ingestion/pipeline.py` and `core/models/ingested_source.py` — both were touched, plus a migration and a new test file, which is normal for a tier-2 DB-touching change.
- **Where the real scope exceeded the estimate:** the pipeline's DB calls were dead code (a string-literal query, a log-only "record" stub), and the codebase's only DB session type is async — so the fix also required converting several methods to `async def`, which the manifest entry didn't call out. Still within tier-2 territory, just more plumbing than the one-line description suggested.
- **Verdict:** right-sized for the tier — self-contained, testable in isolation with mocks (no live Postgres/Chroma needed), and didn't require touching unrelated systems (RAG, agent, safety) to complete.

**Branch name:** feat/13-hashtodetect-unchange

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Reproduction commit link:** https://github.com/hfenelsoftllc/pathreview/commit/ec696bcd5aba1bed6bea7eb6df0ad7c88e93ca5f

**Reproduction summary:**
Read `create_review()` in `core/services/review_service.py` alongside `get_review()`/`list_reviews()` in the same file and confirmed by inspection that `create_review()` accepts a `user_id` argument but never queries `Profile` with it — it builds the `Review` straight from the caller-supplied `profile_id`, unlike its sibling functions which join through `Profile.user_id`. I reproduced this at the test level (TDD "red" step) by writing a unit test that calls `create_review()` with a `profile_id`/`user_id` pair that don't match any owned profile and asserting it returns `None`; against the original code this test failed because `create_review()` never called `db.execute()` at all (0 calls), proving it created a `Review` unconditionally regardless of ownership.

**PLAN.md link:** https://github.com/hfenelsoftllc/pathreview/blob/fix/163-scope-create-review-to-owner/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
GitHub Actions has never run on this fork (0 total workflow runs repo-wide) — forks have Actions disabled by default until manually enabled from the Actions tab — so PR #5 currently has no CI status checks. Proceeding with local `pytest` verification for now; will revisit enabling Actions before Week 9 if CI status is expected on the PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are done. Wrote failing tests first (red) asserting
`create_review()` returns `None` for a `profile_id` not owned by `user_id`, then
implemented the fix (green): `create_review()` now queries `Profile` scoped by
`(id, user_id)` before building the `Review`, returning `None` on no match. Wired
`create_review_endpoint()` to raise `404 "Profile not found"` when that happens,
matching `get_review_endpoint()`'s existing cross-user behavior. Updated the
pre-existing `create_review` tests to mock the new `Profile` lookup.

**Next steps:**
Ran the full unit suite to confirm no regressions, filled in the PR description,
and closed out the Week 9 journal entries.

**Blockers:**
None. (Note: `.venv` in this workspace is WSL/Linux-targeted, not runnable from
native Windows shells directly — had to invoke pytest via `wsl.exe` to verify.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/309

**Branch:** `fix/163-scope-create-review-to-owner`

**What you built:**
Fixed an IDOR / broken object-level authorization bug where `POST /reviews` let
any authenticated user create a review against another user's profile, as long
as they knew or guessed that profile's UUID. `create_review()` now looks up the
`Profile` scoped by `(id, user_id)` before creating the `Review`, returning `None`
if it isn't owned by the caller — the endpoint maps that to a 404, consistent with
how `get_review()`/`list_reviews()` already scope reads.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added 8 new tests covering `create_review()`
ownership: creates review when profile is owned, returns `None` when it isn't,
scopes the DB query correctly, and preserves existing behavior (`pending` status,
`db.add`/`commit`/`refresh` calls). Also updated the pre-existing `create_review`
tests to mock the new `Profile` lookup so they still exercise the owned path.

`tests/unit/test_reviews.py` (new file) — added the repo's first route-level
test, covering `create_review_endpoint()`'s HTTP behavior directly: 404
`"Profile not found"` when `create_review()` returns `None`, and 200 with the
serialized review body when it succeeds. Mounts only `reviews.router` on a bare
`FastAPI()` app with `get_current_user`/`get_db` overridden and
`create_review`/`process_review` patched at the point of use, so it stays a true
unit test (no real DB, no `api.main`'s `startup` → `init_db()` side effect).

**Follow-up cleanup (post Check-in 1):**
Type-checking the new test file surfaced pre-existing `mypy`/`ruff` debt in
`core/services/review_service.py` and `api/routes/reviews.py` (missing
`db: AsyncSession` annotations, two `no-any-return` findings, `Depends()`-in-default
and bare-`raise`-in-`except` bugbear findings) that predates this branch. Fixed
rather than skipped: added the missing annotations, narrowed the `Any` returns via
typed locals, added `from exc` to four bare re-raises, and added
`extend-immutable-calls = ["fastapi.Depends"]` to `pyproject.toml`'s ruff config
(ruff's documented fix for FastAPI's idiomatic `Depends()`-as-default pattern). No
behavior change — verified via WSL pytest (2 new route tests + 8 `create_review`
tests still pass) and `pre-commit run` (ruff/black/mypy all pass on every file this
branch touches).

Also ran a self-review against `docs/CONTRIBUTING.md`: branch name and commit
format are compliant; two commits (`ec696bc`, `7deedb9`) used scope `reviews`
instead of the documented `api`, and touched functions use short one-line
docstrings rather than full Google-style — both flagged as pre-existing/repo-wide
conventions (confirmed via precedent in `profile_service.py`/`profiles.py` and
this repo's own commit history) rather than fixed, since fixing the scope would
mean rewriting already-pushed history on an open PR for a cosmetic deviation.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Scoped to what this branch touches: `ruff`/`black`/`mypy` all pass via
`pre-commit run` on `review_service.py`, `reviews.py`, `test_reviews.py`, and
`pyproject.toml`. Repo-wide `make check`/`make test-unit` still surface pre-existing,
unrelated failures — 152 ruff findings and 49 black reformats elsewhere in the repo,
a `mypy` run that aborts early on missing third-party stubs, and 53 pre-existing
unit test failures (13 in `get_review`/`list_reviews` from the documented `AsyncMock`
issue, 40 more spread across unrelated modules like `test_skill_extractor.py` and
`test_tech_detector.py`) — none introduced by this change, confirmed against the
`main` baseline.)

## Week 10 — Iteration & reflection

This week's iteration wasn't limited to review comments. PR #5 merged the
ownership fix on 2026-07-24, but it was reverted on 2026-07-30
([`fe108fe`](https://github.com/hfenelsoftllc/pathreview/commit/fe108fe7e9ea016363e2324a12a7ec54b8d50e35)),
which stripped the fix, `PLAN.md`, the test file, and the Week 8 journal entry
back out of `main` — restoring the original IDOR bug with zero test coverage
for it. [PR #6](https://github.com/hfenelsoftllc/pathreview/pull/6) re-landed
everything from #5 on top of current `main`, plus the route-level tests and
mypy/ruff cleanup already documented in Week 9.

### Reviewer feedback

**Feedback received:** [*] Yes  [ ] No — still awaiting review

**Summary of feedback:**
The reviewer called the testing approach thorough and said it showed strong
instincts: writing the failing test first, covering both the owned and
not-owned paths, and adding route-level tests that isolate the endpoint from
the real database and startup side effects. Their one suggestion was to
strengthen the database-level tests specifically — they flagged a likely edge
case I hadn't covered, one that could make the suite brittle if the
implementation changed even slightly. The intent behind the suggestion was to
make the test suite resilient to future implementation changes, not just
correct against the current one.

**How you responded:**
Feedback like this is worth treating as a chance to learn rather than a note
to clear. I agree with the direction — database-level testing is a
notoriously easy place for a suite to end up coupled to implementation
details instead of behavior. That said, I haven't written the additional
edge-case test yet; it's the immediate next step before I'd consider this
branch fully iterated on, not something already landed in a commit.
---

### Reflection

**What was harder than you expected?**
I'd never worked in an OSS codebase before, and the sheer volume of
information was overwhelming — figuring out which part of the problem to
tackle, and understanding the application's objectives well enough to
calibrate my work against the specific issue I was targeting.

**What did you learn about working in a large codebase?**
I'm already comfortable with large codebases from work experience, but
always in a structured setting — a Jira board where you pick which epic or
sprint task to work on from a backlog. I try to replicate that structure on
my own projects too, using GitHub's project management features to define
everything on my own backlog as issues.

**How did AI tools help — and where did they fall short?**
AI tools were most useful during the implementation phase — once the plan
was set, they let me move noticeably faster on code delivery.

**What would you do differently if you started over?**
For implementation specifically, I'd lean on AI tools again — they saved a
meaningful amount of time on code delivery.

**What are you most proud of from this module?**
Learning this new way of building software: one where I structure my
planning steps up front and feed the AI more context about my choices and
objectives before it writes any code.