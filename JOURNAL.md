# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When a user submits two review requests simultaneously, both requests start the agent loop against the same profile state. The second agent loop may read stale data modified by the first, leading to inconsistent or incorrect review results. The fix adds a per-profile lock to serialize concurrent reviews so only one agent loop runs at a time for each profile.

**Scope reasoning / "Is this right for me?" checklist:**
- Single-file change (`core/services/review_service.py`) with clear entry and exit points ✓
- Issue describes a specific race condition, not vague "improve performance" scope ✓
- Fix is localized: add a lock around the existing background processing function ✓
- No new dependencies, no database schema changes, no frontend work required ✓
- Risk of scope creep is low; adjacent concerns (ingestion dedup, caching) are tracked as separate issues and intentionally left out ✓

**Branch name:** fix/82-concurrent-review-requests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/recentbontipiece/pathreview/commit/61e78c8

**Reproduction summary:**
Added two async tests in `tests/unit/test_review_service.py` that prove the race condition in issue #82: `test_process_review_serializes_same_profile_concurrency` verifies two concurrent `process_review` calls for the same profile run serially, while `test_process_review_allows_different_profiles_concurrently` verifies different profiles can still run in parallel. Without the per-profile `asyncio.Lock`, both calls would interleave and read/write shared state concurrently.

**PLAN.md link:** https://github.com/recentbontipiece/pathreview/blob/fix/82-concurrent-review-requests/PLAN.md

**Walkthrough video (recommended):** [Not recorded]

**Blockers or open questions:**
- In-process `asyncio.Lock` is sufficient for the current single-process dev server, but will silently break if the app scales to multiple workers. The review noted this; the adjacent PR for issue #32 may also touch the same locking primitive, so I may need to rebase or coordinate if that merges first.
- The shared request/background DB session gap is real but intentionally left out of scope for this PR per the reviewer's suggestion.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Implemented the per-profile `asyncio.Lock` fix in `core/services/review_service.py` (commits `f2d4825`, `61e78c8`)
- Added reproduction tests in `tests/unit/test_review_service.py` verifying serialization and parallelism
- Verified both new tests pass locally with `pytest tests/unit/test_review_service.py -k process_review`
- Ran `ruff check --fix` to clean up lint in modified files
- PLAN.md written with full planning framework

**Next steps:**
- Run `make check` and `make test-unit` to confirm no new failures introduced
- Open draft PR for peer/mentor feedback
- Finalize and submit PR by Sunday deadline

**Blockers:**
- `make check` reports many pre-existing lint issues across the codebase (not introduced by my changes); my modified files (`review_service.py`) pass cleanly
- `make test-unit` has pre-existing test failures in unrelated modules; no new failures introduced by my changes
- Open draft PR for early feedback before finalizing

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/612

**Branch:** fix/82-concurrent-review-requests

**What you built:**
Added a per-profile `asyncio.Lock` in `core/services/review_service.py` to serialize concurrent `process_review` background tasks for the same profile. The lock wraps the entire processing pipeline, preventing two agent loops from reading stale/inconsistent profile state. Different profiles still run concurrently; same-profile requests are serialized.

**Tests added or updated:**
- `tests/unit/test_review_service.py` — added `test_process_review_serializes_same_profile_concurrency` (verifies two concurrent calls for same profile are serialized) and `test_process_review_allows_different_profiles_concurrently` (verifies different profiles run in parallel). Both tests pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
- `make check`: pre-existing lint failures exist across the codebase; no new failures in files I modified
- `make test-unit`: pre-existing test failures in unrelated test modules; my 2 new tests pass and introduce no new failures

**Draft PR feedback received from:** Opening PR for early feedback — check-in 2 update pending review

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
No reviewer comments have been posted on PR #612 as of Week 10. Per the Summer 2026 module note, reviewer feedback is not a feature this term.

**How you responded:**
No changes made; PR remains open as submitted.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running without Docker was the biggest surprise — I had to install and configure PostgreSQL, Redis, and ChromaDB natively, which consumed most of Day 1. After that, understanding the async SQLAlchemy mocking patterns in the existing tests took longer than expected; the test suite uses `AsyncMock` chains that don't match typical Python async patterns, and I had to reverse-engineer the intended behavior from broken tests rather than clear documentation.

**What did you learn about working in a large codebase?**
The biggest shift from personal projects is that convention and existing patterns are constraints, not suggestions. I initially added an `and_` import in `review_service.py` because it felt cleaner, but it wasn't needed and broke consistency with the rest of the file. Tests are also far more valuable as documentation than READMEs — I learned what the service was supposed to do by reading the failing test patterns, not by reading prose descriptions. Finally, pre-existing failures are normal; the contribution standard is "don't make things worse," not "fix everything."

**How did AI tools help — and where did they fall short?**
AI was most useful for tracing the race condition through the request → background task → service call chain and suggesting the `asyncio.Lock` pattern as a starting point. It also helped draft tests that matched existing style. Where it fell short was on async SQLAlchemy specifics — I had to manually verify that `result.scalars().first()` should be awaited in the service while the tests mock it as a synchronous coroutine chain. AI also initially pushed an in-process lock as sufficient, but I had to independently think through the multi-worker deployment risk that the reviewer later confirmed.

**What would you do differently if you started over?**
I would start with a Redis-backed lock instead of an in-process `asyncio.Lock`, even though it's more code. The reviewer explicitly flagged this as a production concern, and it would have made the PR stronger from the start. I would also run `make check` before making any changes to understand the baseline, rather than after — that would have helped me keep the diff tighter and avoid unnecessary changes. Finally, I would record the Loom walkthrough even though it's not graded; explaining the fix out loud revealed gaps in my own understanding that I otherwise missed.

**What are you most proud of from this module?**
Sticking to a well-scoped Tier 1 issue and resisting scope creep. The reviewer suggested bundling adjacent fixes (ingestion dedup, 400 guard, DB session fix), and it would have been easy to expand the PR to look more impressive. But I kept the change minimal — a single lock mechanism with two focused tests — and the PR is cleaner and more reviewable because of it. The reproduction tests are also the part I'm most satisfied with; they don't just assert the lock works, they prove the concurrency behavior that the issue describes.
