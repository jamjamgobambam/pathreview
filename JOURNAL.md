## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker combines the text from retrieved context chunks before evaluating an AI-generated statement. When a chunk contains a `text` key whose value is `None`, the current use of `dict.get()` returns `None` instead of the empty-string default. Passing that value to `" ".join()` raises a `TypeError`, causing the evaluation to stop. A successful fix will handle null text safely, preserve valid context text, and pass the related unit test.

**Selection notes:**
The issue has a small and clearly defined scope within the faithfulness checker. It includes a direct reproduction example and an existing related unit test, so I can verify the behavior locally. It does not require a paid API or an architectural change, and success is clearly defined as handling `None` without crashing.

**Branch name:** fix/153-faithfulness-none-context

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Issue reproduction and solution planning

**Reproduction status:** [x] Issue reproduced locally

**Reproduction command:**

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v
```

**Observed result:**
The test failed with `TypeError: sequence item 0: expected str instance, NoneType found` in `rag/evaluator/faithfulness_checker.py`.

**Expected result:**
The checker should handle a context chunk containing `{"text": None}` without crashing and return a valid float score.

**Root cause:**
`chunk.get("text", "")` returns the empty-string default when the key is missing, but it returns `None` when the key exists with a null value. The resulting list is passed to `" ".join()`, which only accepts strings. This causes the checker to crash before calculating its score.

**Files investigated:**

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`
- `rag/evaluator/eval_suite.py`
- `rag/evaluator/relevance_scorer.py`

**Solution plan:** [PLAN.md](./PLAN.md)

**Planned scope:**
Normalize missing or null context text inside `FaithfulnessChecker.check()` while preserving valid text and leaving the scoring algorithm unchanged. The similar behavior in `RelevanceScorer` is outside the scope of issue #153.

**Walkthrough video:** [ ] Optional video completed

## Week 9 — Build and pull request

### Check-in 1 — Implementation and draft PR

**Progress:**
I implemented the fix for issue #153 by normalizing missing or null context text to an empty string before joining the chunks. I strengthened the existing regression test and added a test confirming that a null chunk does not discard text from another valid chunk.

**Verification:**

- Focused regression tests: 2 passed
- Full faithfulness test file: 20 passed, 3 pre-existing scoring failures
- `make check`: 182 pre-existing errors before and after the change
- `make test-unit` before: 53 failed, 375 passed
- `make test-unit` after: 52 failed, 377 passed
- No new test failures were introduced

**Draft pull request:** https://github.com/ascherj/pathreview/pull/919

**Current blockers:**
The repository still has pre-existing lint, typing, and unrelated unit-test failures. They do not block the issue-specific correction.

**Next step:**
Request peer feedback, respond to the review, run the final checks, and mark the pull request ready for review.

## Week 10 — Iteration & reflection

### Reviewer feedback

*Feedback received:* [ ] Yes  [x] No — still awaiting review

*Summary of feedback:*
No reviewer or maintainer feedback has been received yet. The pull request is open and ready for review, but its workflows and merge remain pending maintainer approval.

*How you responded:*


---

### Reflection

*What was harder than you expected?*
The hardest part was separating problems caused by my change from problems that already existed in the repository. The baseline had 182 lint errors and 53 failing unit tests before implementation. When I attempted to commit, Ruff and Black modified the staged Python files, while mypy reported 26 existing annotation errors in the test file. I had to understand Git staging, restore only the hook-generated working-tree changes, preserve my intended diff, and document the baseline failures instead of expanding the issue into a repository-wide cleanup.

*What did you learn about working in a large codebase?*
I learned that contributing to someone else's codebase requires controlling scope and collecting evidence before changing anything. I first reproduced the exact ⁠ TypeError ⁠, identified how ⁠ dict.get("text", "") ⁠ still returns ⁠ None ⁠ when the key exists, and recorded the test and lint baseline. I kept the fix limited to ⁠ FaithfulnessChecker ⁠ even though I noticed similar behavior in ⁠ RelevanceScorer ⁠, because that was outside issue #153. Unlike building my own project, I could not treat every problem I encountered as part of my task. I had to follow the repository's Git workflow, tests, formatting tools, and review process.

*How did AI tools help — and where did they fall short?*
AI assistance helped me understand the unfamiliar codebase, trace the failure to Python's ⁠ dict.get() ⁠ behavior, compare possible fixes, and design regression coverage for both an all-null context and a mixture of null and valid chunks. It also helped me interpret test output and prepare the pull request documentation. However, AI-generated changes did not initially account for the repository's full pre-commit behavior: Ruff and Black reformatted the files, and mypy exposed many existing errors. I still needed to inspect the staged and unstaged diffs, verify which failures were pre-existing, make the scope decision myself, and ensure the final PR contained only intentional changes.

*What would you do differently if you started over?*
I would run the repository's pre-commit hooks and focused tests on the target files immediately after reproducing the issue, before implementation. That would reveal formatting, lint, and typing problems earlier. I would also record the baseline results in one place from the beginning and open the draft PR as soon as the first tested commit was available. I would still choose this issue because its scope and success criteria were clear, but I would plan the validation and commit workflow earlier.

*What are you most proud of from this module?*
I am most proud that I completed the full contribution cycle instead of stopping after writing a one-line fix. I reproduced the bug, explained its root cause, added regression coverage, compared the complete test suite before and after the change, documented the repository's existing failures honestly, and submitted PR #919 without introducing any new test failures.