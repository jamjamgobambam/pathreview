## Week 7 - Issue selection

**Issue link:** [Issue #157](https://github.com/ascherj/pathreview/issues/157)

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue is in the RAG evaluation test suite, specifically `tests/unit/test_relevance_scorer.py`. The test named `test_query_with_partial_overlap` is supposed to verify that partially matching content produces a middle-range relevance score, but its fixture text actually contains all of the query terms. Because the scorer correctly treats that as full overlap, the test fails even when the production code is behaving as intended. A successful fix would update the fixture so it represents a true partial-overlap case and makes the test validate the intended behavior.

**Branch name:** `fix/157-relevance-scorer-partial-overlap-fixture`

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes / scope reasoning:**
I chose this issue because it is Tier 1, isolated to a single test file, and easy to understand from both the issue description and the local code. The expected change is small and low-risk, which makes it a strong first contribution for Module 3. It also gives me a clear path to verify the fix with a focused unit test once the local Python environment is available in Git Bash.

**Setup notes:**
As of July 22, 2026, this repo is cloned from my fork and already has `upstream` configured, but I have not yet confirmed the app at `localhost:5173`. The local Windows setup is still blocked because Git Bash is installed, but `python` is not currently available there, so `make setup` cannot complete yet.

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** [25c4fb1](https://github.com/averiedayimshufflin/pathreview/commit/25c4fb1)

**Reproduction summary:**
I reproduced the issue by tracing `test_query_with_partial_overlap` against `RelevanceScorer.score` and confirming that the current chunk fixture contains all four query tokens. That produces full overlap and a score of `1.0`, so the test fails because it claims to be exercising a partial-match case while actually setting up a perfect-match fixture.

**PLAN.md link:** [PLAN.md](https://github.com/averiedayimshufflin/pathreview/blob/fix/157-relevance-scorer-partial-overlap-fixture/PLAN.md)

**Walkthrough video (recommended):** 

**Blockers or open questions:**
I still need the local Python test environment available to run the focused unit test and confirm the exact post-fix score in code, but the root cause of the current failure is clear from the existing test data and scoring logic.

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the test fix in `tests/unit/test_relevance_scorer.py` by replacing the full-overlap fixture with a true partial-overlap fixture. I also tightened the assertion so the test now checks the expected partial-overlap score directly (`0.5`) instead of relying on a broad middle-range check.

**Next steps:**
My next steps are to run the relevant unit tests, confirm `make test-unit` and `make check` do not introduce any new failures, and then open a PR to `pathreview` with the completed template and issue context.

**Blockers:**
As of Tuesday, August 4, 2026, I still cannot run Python from this Codex workspace because the local interpreter is not available through the sandboxed shell, so test verification needs to be completed from my local development terminal.

---

### Check-in 2 (end of week)

**PR link:** 

**Branch:** `fix/157-relevance-scorer-partial-overlap-fixture`

**What you built:**

**Tests added or updated:**

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** 
