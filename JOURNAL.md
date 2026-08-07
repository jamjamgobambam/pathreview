## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/32)

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1 [X] Tier 2 [ ] Tier 3

**Problem summary:**

The issue is that duplicate portfolio submissions will cause the RAG llm system to run on the
same object again. What's missing is a caching behavior to reduce this inefficency, and thus the
goal is to cache the response so that if the portfolio hasn't changed
since the last run, then it could just return the previous run's results instead. A sucessful fix
would implement this behavior. this should affect the review services.

**Branch name:** fix/32-query-caching

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Scope fit**

How many others are already working on this issue?

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
Is the scope realistic for Weeks 8–9?

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
Are there any blockers or dependencies?

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[X] This issue has no open blockers or dependencies on other unresolved issues.

---

I picked this issue since I know about caching and wanted more practice in RAG pipelines.
I would say that I am used to large codebases so this isn't that much of a concern for me, so I thought that
tier 2 would be fitting for me.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/KadenXu5001/pathreview/commit/077df9a284e8e7483ea4e3660c73e26298042584

**Reproduction summary:**
This wasn't really an issue but rather a new feature implementation. But what I did was to make a unit test that fails if when given the same 2 portfolios, it fails if the run command happens twice.

**PLAN.md link:** [Link text](PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the Redis-backed review cache from PLAN.md. Cache keys are isolated by user and derived from normalized portfolio content. Identical submissions reuse cached RAG output, while changed resume content creates a cache miss. Redis failures fall back to normal generation.

**Next steps:**
Open a draft PR, request peer or mentor feedback, address accepted feedback, and complete final testing and submission documentation.

**Blockers:**
The repository has pre-existing failures in its full unit and repository-wide lint suites. The cache-focused tests and checks for all changed files pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/287

**Branch:** `fix/32-query-caching`

**What you built:**
Implemented a Redis-backed caching layer for repeated portfolio reviews. The cache uses user-scoped, deterministic content hashes to reuse successful RAG output while treating Redis failures or invalid cached data as cache misses.

**Tests added or updated:**
Added `tests/unit/test_review_cache.py` and updated `tests/unit/test_review_service.py`. The tests cover deterministic hashing, user isolation, content changes, TTL behavior, cache hits, malformed data, Redis failures, and ensuring safety-rejected results are not cached.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

The repository has documented pre-existing failures in the full check and unit-test suites. Under the course's pre-existing-failure policy, the cache-focused tests and Ruff, Black, and Mypy checks for every changed file pass, and these changes introduce no new failures.

**Draft PR feedback received from:** Christopher Castro

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
As of August 6, 2026, PR #287 has not received a formal review, maintainer
comment, or inline review comment. The peer feedback recorded in Week 9 was part
of the draft PR process rather than formal reviewer feedback.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was deciding what "identical" meant in a real ingestion
pipeline. A cache key based on profile or review IDs would never be reusable,
while a key based on filenames could return a stale result after the resume
content changed. I had to identify transient fields, canonically serialize the
actual ingested content, and hash it while still scoping the key to one user. so
Integrating the cache was also more delicate than simply wrapping the RAG call:
cached output still needed to pass the existing safety checks, and a Redis
failure could not be allowed to fail the review itself.

**What did you learn about working in a large codebase?**
I learned that the surrounding contracts matter as much as the feature code.
Before implementing anything, I had to trace `process_review()` through
ingestion, agent orchestration, RAG generation, safety validation, and database
persistence. I also had to notice that Redis and its configuration already
existed instead of introducing a second caching dependency. In someone else's
production code, a locally correct shortcut can still violate privacy, status
transitions, logging conventions, or failure behavior. The safest approach was
to keep the API unchanged, place the cache at one narrow point in the service,
and add tests for user isolation, invalid data, TTL use, and unavailable Redis.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for quickly mapping unfamiliar modules, turning the
issue into an implementation plan, and suggesting edge cases such as malformed
cached JSON, source ordering, user isolation, and safety-rejected output. They
also helped draft focused tests and interpret failures. However, AI could not
decide product questions that the repository did not answer, such as the ideal
TTL or whether concurrent identical requests required a distributed lock. I
still had to inspect the actual control flow, verify every suggestion against
the repository's types and conventions, and determine which suite failures were
already present. AI accelerated the investigation, but it did not replace
repository knowledge or engineering judgment.

**What would you do differently if you started over?**
I would run and record the complete baseline test, lint, formatting, and type
check results before changing code. That would make pre-existing failures easier
to separate from regressions later. I would also ask the maintainer about cache
TTL, invalidation policy, and concurrent requests during issue selection rather
than carrying those as open assumptions. During implementation, I would keep
the first commit more narrowly focused on the failing reproduction test and
avoid touching unrelated mocks until I knew exactly which changes were required
for the cache tests.

**What are you most proud of from this module?**
I am most proud that the caching feature is defensive instead of only working on
the happy path. The implementation avoids putting raw portfolio content in Redis
keys, prevents cache sharing across users, re-runs safety checks on cached data,
rejects malformed entries, and falls back to normal generation when Redis is
unavailable. The tests capture those guarantees, so the contribution improves
performance without silently weakening privacy or reliability.

Thank you guys for all the work in this free course btw!
