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

**PR link:** [PR #718](https://github.com/ascherj/pathreview/pull/718)

**Branch:** `fix/157-relevance-scorer-partial-overlap-fixture`

**What you built:**
I fixed the `test_query_with_partial_overlap` fixture in `tests/unit/test_relevance_scorer.py` so it now represents a true partial-match case instead of a perfect match. The test now asserts the exact expected score of `0.5`, which matches the scorer's current overlap logic and makes the test validate the intended behavior.

**Tests added or updated:**
I updated `tests/unit/test_relevance_scorer.py`. The focused relevance scorer test file passes locally, including the corrected partial-overlap case.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
Note: the repository still has many pre-existing unrelated failures in `tests/unit` and code-quality checks, including failures in `bias_detector`, `faithfulness_checker`, `pii_scrubber`, `review_service`, `skill_extractor`, `tech_detector`, and existing Ruff issues in unrelated files. My change is isolated to `tests/unit/test_relevance_scorer.py`, and the focused relevance scorer test file passes after the fix.

**Draft PR feedback received from:** none

## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No formal maintainer or reviewer feedback has come in yet for [PR #718](https://github.com/ascherj/pathreview/pull/718). That matches the Summer 2026 course note that reviewer feedback is not expected this term. The main guidance I worked from instead was the issue description, the existing test suite, and the contribution standards around keeping a fix narrowly scoped and clearly documenting verification.

**How you responded:**
I kept the change limited to the failing relevance scorer test fixture, verified the focused test file locally, and documented the unrelated repository-wide failures separately so I would not overstate what my change fixed.

---

### Reflection

**What was harder than you expected?**
The hardest part was separating the actual bug from the test's wording. At first glance, `test_query_with_partial_overlap` sounded like it was checking a production-code edge case, but the issue was really that the fixture contradicted the scenario. I had to slow down and trace how `RelevanceScorer.score` tokenized the query and chunk text before changing anything. It was also harder than expected to document the local test situation clearly because some repository-wide checks had unrelated pre-existing failures, so I needed to be precise about what my change did and what I could verify.

**What did you learn about working in a large codebase?**
I learned that even a small one-line fixture change needs context. In my own projects, I might rewrite the test or scorer quickly, but in someone else's codebase I needed to preserve the existing scoring behavior and make the smallest change that matched the issue. The surrounding tests helped define the intended contract: exact matches score high, no overlap scores zero, and partial overlap should land between those. I also learned to read tests as part of the codebase's documentation, because the bug was not just a failing assertion; it was a misleading example of the behavior the project wanted to guarantee.

**How did AI tools help - and where did they fall short?**
AI tools were most helpful for navigating the repository, comparing the issue description against the test file, and turning my notes into a clear plan and PR explanation. They helped me keep the scope small instead of overthinking the scorer implementation. Where they fell short was final judgment: AI could suggest likely causes, but I still had to inspect the actual scorer logic, confirm which words overlapped, and decide that the production code should not change. AI also could not replace the need to understand the course workflow, the branch URL requirement, and the difference between focused test results and unrelated repository-wide failures.

**What would you do differently if you started over?**
I would set up the local environment earlier and verify the focused test before writing as much documentation. I would also check the exact token overlap by hand sooner, because that made the fix obvious: the old fixture included every query term, while the corrected fixture needed to include only some of them. For the process side, I would keep a shorter running note of commands, blockers, and verification results each week so the journal entries would be easier to assemble at the end.

**What are you most proud of from this module?**
I am most proud that I kept the contribution small, specific, and honest. The fix did not try to make the project bigger or more impressive than the issue required; it corrected the test so future contributors can trust what that case is supposed to prove. I also documented the limitations around testing instead of hiding them, which feels like a real part of contributing professionally.
