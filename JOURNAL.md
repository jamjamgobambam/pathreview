# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/32

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review pipeline does no work-deduplication: every time a portfolio is
submitted, the full RAG pipeline runs from scratch, even when the exact same
profile was reviewed moments earlier with no changes. This wastes compute and
adds latency (and LLM cost) for a result that is guaranteed to be identical.
The fix introduces a caching layer keyed on a hash of the profile's content, so
an unchanged portfolio short-circuits to the previously stored review instead of
regenerating it. Success means a repeated identical submission returns the cached
review quickly, while any change to the portfolio content produces a new hash and
triggers a fresh generation. This work touches the RAG generator
(`rag/generator/review_generator.py`) and the review service
(`core/services/review_service.py`).

**Branch name:** feat/32-portfolio-query-cache

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sujalusa/pathreview/commit/b59487974ded0caedea73a255f2bc3aff84bb3b1

**Reproduction summary:**
I added an xfail unit test (`tests/unit/test_review_cache_reproduction.py`) that
calls `process_review` twice for the same unchanged profile and asserts the
expensive RAG generation step runs only once. It fails today (RAG runs twice),
confirming there is no caching layer: identical submissions re-run the full
pipeline in `core/services/review_service.py`.

**PLAN.md link:** https://github.com/sujalusa/pathreview/blob/feat/32-portfolio-query-cache/PLAN.md

**Walkthrough video (recommended):** [optional — add Loom link if recorded]

**Blockers or open questions:**
Deciding cache scope: hashing the four `Profile` content fields (github_username,
portfolio_url, resume_text, resume_filename) should satisfy "if the portfolio
hasn't changed," but I need to confirm whether ingested-source content must also
be included. Also deciding whether to add a Redis fast path or rely solely on a
`reviews.content_hash` DB lookup for the first pass.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All implementation sub-tasks from PLAN.md are done. I added an indexed
`content_hash` column to the `Review` model with Alembic migration `003`
(sub-tasks 1–2), implemented `compute_profile_content_hash()` and
`_find_cached_review()`, and wired a cache short-circuit into `process_review()`
so an unchanged portfolio reuses the stored review instead of re-running the
ingestion → agent → RAG → safety pipeline (sub-tasks 3–4). I converted the Week 8
xfail reproduction into passing hash + cache hit/miss tests (sub-task 5). I chose
the DB-lookup approach for the first pass and deferred the optional Redis fast
path to keep the change focused.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md`, run `make check` / `make test-unit`
and confirm no new failures vs. the documented pre-existing baseline, open a
draft PR for peer feedback, then mark it ready for review.

**Blockers:**
None. (Local Postgres wasn't running so I verified the migration is linear
001→002→003 statically rather than applying it live; unit tests don't need the DB.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1035

**Branch:** `feat/32-portfolio-query-cache`

**What you built:**
A caching layer for portfolio reviews. `process_review` now computes a SHA-256
hash of the profile's content fields and, if a completed review with the same
hash already exists for that profile, returns the stored result without
re-running the RAG pipeline; otherwise it generates the review and persists the
hash for next time.

**Tests added or updated:**
`tests/unit/test_review_cache_reproduction.py` — 6 tests covering hash
determinism/content-sensitivity, a cache hit skipping the pipeline and reusing
the stored result, and a cache miss running the pipeline once and persisting the
hash.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!-- "passes" = introduces no new failures vs. the pre-existing baseline documented
in the PR: ruff 182, black 52, mypy red, test-unit 53 failed on main. My touched
files are ruff/black clean and my new functions are mypy-clean; test-unit stays at
53 pre-existing failures with 6 new passing tests. -->

**Draft PR feedback received from:** none yet (draft PR to be shared in Slack)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided this term (Summer 2026 does not include peer/
mentor PR review). The PR was opened against the upstream repo and submitted; no
comments came in to respond to.

**How you responded:**
N/A — no feedback to address. If I were iterating, the first thing I'd revisit
from my own self-review is adding an integration test that applies migration
`003` and exercises the cache hit path against a real Postgres session, since my
unit tests mock the DB.

---

### Reflection

**What was harder than you expected?**
Proving my change didn't make things worse in an already-broken codebase was far
harder than writing the fix itself. When I ran the baseline, `main` was deeply
red: 182 ruff errors, 52 files unformatted, mypy failing, and 53 failing unit
tests. So "does it pass?" became "does it pass *relative to baseline?*". Concretely,
my new cache tests ran alongside 13 failures in `test_review_service.py`, and I
had to `git stash` my source changes and re-run that file against the original
code to confirm those 13 were pre-existing and not mine. That verification loop —
not the caching logic — ate most of my time. The pre-commit `mypy` hook also
blocked commits on pre-existing type debt, so I had to consciously `SKIP=mypy`
and document why, rather than "fixing" errors that weren't mine.

**What did you learn about working in a large codebase?**
The biggest shift from my own projects is that I don't get to trust the ground I'm
standing on. In my own code, green means green; here, the existing tests were
themselves broken (the async DB mocks raised "coroutine was never awaited"), so I
couldn't just copy the nearest test pattern — I had to build a cleaner stateful
mock and patch `_find_cached_review` directly instead of faking opaque SQLAlchemy
statements. I also learned to respect boundaries: the disciplined move was to make
*only* my touched files clean and leave the repo-wide debt alone, because a PR
that also reformats 52 unrelated files is unreviewable. Matching conventions
(commit scopes, the `002` migration pattern, Google-style docstrings) mattered
more than being clever.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and mechanical correctness: quickly reading
`review_service.py` + the models + the migration pattern to locate the exact root
cause (`process_review` unconditionally re-running the pipeline), and scaffolding
the migration, hash helper, and test boilerplate in the house style. It fell short
on judgment calls that depended on *this* assignment's rules — e.g., deciding that
53 pre-existing test failures were acceptable to leave, or that the compare/PR
step needed a human because `gh` wasn't installed and auth is interactive. It also
couldn't close the runtime loop: the local Postgres container was down, so neither
I nor the tooling could actually apply migration `003` end-to-end — that gap is
real and only a running environment (or an integration test) fixes it.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` on day one of Week 7, before reproduction,
so I'd know the baseline was red going in instead of discovering it mid-implementation
in Week 9 — it would have reshaped how I framed "passing" from the start. I'd also
open the draft PR earlier (Week 8, right after the reproduction) to get eyes on the
approach before building, and I'd stand up the Postgres container so I could apply
the migration and add one integration test rather than relying entirely on mocked
DB sessions.

**What are you most proud of from this module?**
The reproduction-first discipline. In Week 8 I wrote an `xfail(strict=True)` test
that pinned the exact gap and stayed green in CI; in Week 9 that same test flipped
to passing the moment the cache landed, giving me an objective before/after proof
that the fix does what the issue asked. Pairing that with a documented baseline so
I could honestly claim "zero new failures" in a broken repo felt like real
engineering, not just getting code to run.
