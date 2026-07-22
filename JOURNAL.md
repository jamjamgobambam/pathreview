## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/32

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
If a user submits the same portfolio twice without editing anything, they sit through the full review process again and get back feedback they already had. Nothing in that path checks for prior work, create_review() in core/services/review_service.py just starts another pending review, and retrieval and generation run from scratch every time. So identical input costs the same time and API calls it cost the first time, and leaves a duplicate entry in the user's review history. A successful fix would key a cache on a hash of the profile's content, return the stored review when nothing has changed, and regenerate only when it has. I chose this Tier 2 issue because RAG systems and hand-rolled LLM caching are both things I have worked with in this class and in personal projects recently, so the concepts are familiar, and the real stretch for me is working inside an unfamiliar codebase and getting the invalidation right.

**Branch name:** feat/32-portfolio-query-cache

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
