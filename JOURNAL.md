## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/32

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
If a user submits the same portfolio twice without editing anything, they sit through the full review process again and get back feedback they already had. Nothing in that path checks for prior work, create_review() in core/services/review_service.py just starts another pending review, and retrieval and generation run from scratch every time. So identical input costs the same time and API calls it cost the first time, and leaves a duplicate entry in the user's review history. A successful fix would key a cache on a hash of the profile's content, return the stored review when nothing has changed, and regenerate only when it has. I chose this Tier 2 issue because RAG systems and hand-rolled LLM caching are both things I have worked with in this class and in personal projects recently, so the concepts are familiar, and the real stretch for me is working inside an unfamiliar codebase and getting the invalidation right.

**Branch name:** feat/32-portfolio-query-cache

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/codyholm/pathreview/commit/163ae55

**Reproduction summary:**
Submitted the same unchanged profile twice via `POST /reviews` and observed two distinct reviews created, the full pipeline running twice in the server logs with byte-identical output (same sections, same 0.81 score), and the profile's review history growing from 3 to 5 rows. The reproduction commit adds `tests/unit/test_review_cache.py`, whose 6 failing tests pin the expected caching behavior — return the stored review when profile content is unchanged — against the current code in `core/services/review_service.py`, which unconditionally creates a new review on every submit.

**PLAN.md link:** https://github.com/codyholm/pathreview/blob/feat/32-portfolio-query-cache/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
None