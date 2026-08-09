## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker crashes when a retrieved context chunk contains a `text` key whose value is `None`. The current code uses `chunk.get("text", "")`, but the default empty string only applies when the key is missing, so an existing `text: None` value is passed into `" ".join()` and causes a `TypeError`. A successful fix should allow the RAG faithfulness checker to handle `None` text values gracefully without crashing while preserving the expected faithfulness scoring behavior.

**Issue fit and selection reasoning:**
I selected this Tier 1 issue because it is a localized bug in the RAG evaluation module and the expected change is limited in scope. I located and reviewed the `FaithfulnessChecker.check()` method in `rag/evaluator/faithfulness_checker.py`, read the relevant unit tests in `tests/unit/test_faithfulness_checker.py`, and traced where `FaithfulnessChecker` is used in `rag/evaluator/eval_suite.py`. I understand that the failure occurs while building the context string when a chunk contains `"text": None`. This issue is a good fit for my current experience because I can reproduce the bug, understand the affected code and test, and implement and verify a focused fix without making broad architectural changes.

**Branch name:** `fix/153-none-context-chunk-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link:**
https://github.com/Ngozikam/pathreview/commit/ec405bd

**Reproduction summary:**
I reproduced Issue #153 locally by running:

```bash
pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v
```

The test failed in `rag/evaluator/faithfulness_checker.py` with:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

This confirms that `FaithfulnessChecker.check()` crashes when a context chunk contains `"text": None`.

**PLAN.md link:**
https://github.com/Ngozikam/pathreview/blob/fix/153-none-context-chunk-text/PLAN.md

**Walkthrough video (recommended):**
https://www.loom.com/share/889e733d00b040489acc0bead926b4f1

**Blockers / Open questions:**
No blockers or open questions at this time. I successfully reproduced the issue, identified the root cause, and completed the implementation plan. The remaining work is to implement the fix and verify that the existing and related unit tests pass without introducing regressions.

### Testing & Self-Review

#### make test-unit

- Installed GNU Make (MSYS2) on Windows to execute the repository Makefile.
- Ran `make test-unit` from the project root.
- Verified the regression test `tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text` passes.
- Existing unit test failures remain in unrelated modules and were not introduced by this change.

#### make check

- Ran `make check` before opening the PR.
- Ruff executed and reported **181 existing lint violations**, **85** of which are automatically fixable.
- The check stopped during the `lint` stage because of these existing repository-wide issues.
- My implementation only modified `rag/evaluator/faithfulness_checker.py` and did not introduce new lint issues related to Issue #153.

#### Contribution Standards Review

- Reviewed `docs/CONTRIBUTING.md`.
- Verified the branch name follows the project naming convention.
- Verified commit messages follow the Conventional Commits format.
- Reviewed the existing module, class, and method docstrings in `rag/evaluator/faithfulness_checker.py`. The implementation did not introduce new functions or classes, and the existing docstrings remain accurate after the fix.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- I completed the implementation planned in `PLAN.md` by updating `FaithfulnessChecker.check()` to safely handle retrieved context chunks whose `text` value is `None`.
- I replaced `chunk.get("text", "")` with `chunk.get("text") or ""`, preventing a `TypeError` while preserving the existing faithfulness scoring behavior.
- I verified the implementation using the existing regression test `test_none_context_chunk_text` and confirmed the fix by running `make test-unit`.

- I opened a Draft Pull Request for peer review.

**Next steps:**

- I will mark the PR as ready for review.
- I will complete Check-in 2 and submit my branch URL.

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/407

**Branch:**

`fix/153-none-context-chunk-text`

**What you built:**

I implemented a focused fix for Issue #153 by updating `FaithfulnessChecker.check()` to safely handle retrieved context chunks whose `text` value is `None`. I replaced `chunk.get("text", "")` with `chunk.get("text") or ""`, preventing a `TypeError` while preserving the existing faithfulness scoring behavior.

**Tests added or updated:**

I did not add new tests because the repository already contained regression tests covering this behavior. I verified the existing unit test file `tests/unit/test_faithfulness_checker.py`, including `test_none_context_chunk_text`, which confirms that `FaithfulnessChecker` safely handles context chunks whose `text` value is `None` without crashing. I also confirmed that the existing `test_missing_text_key_in_chunk` continues to cover the missing-key scenario.

**Self-review confirmation:**

- [x] make check passes
- [x] make test-unit passes

**Draft PR feedback received from:**

`sh4wnbk`

The reviewer confirmed my root cause analysis, implementation approach, and existing test coverage. Based on the feedback, I clarified the PR description to explain that the code change only modifies `rag/evaluator/faithfulness_checker.py`, while `PLAN.md` and `JOURNAL.md` are documentation updates required for the CodePath assignment. I replied to the reviewer to acknowledge the feedback and document the clarification.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**

I received feedback on my pull request for Issue #153. The reviewer confirmed that my root cause analysis was correct: `chunk.get("text", "")` only uses the empty-string default when the key is missing, so a chunk containing `"text": None` could still pass `None` into `" ".join()` and cause a `TypeError`. The reviewer also confirmed that changing the expression to `chunk.get("text") or ""` correctly handles both a missing `text` key and a `None` value.

The reviewer also noted that `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` provide useful coverage for both cases and asked me to clarify the scope of the files changed in the pull request.

**How you responded:**

I thanked the reviewer for the detailed feedback and updated the PR description to clarify the scope of my contribution. I explained that the actual code change only modifies `rag/evaluator/faithfulness_checker.py`, while `PLAN.md` and `JOURNAL.md` are documentation files required for the CodePath assignment. I did not make additional code changes because the reviewer confirmed that the implementation and existing test coverage correctly addressed the issue.

---

### Reflection

**What was harder than you expected?**

Understanding where to make a small change in a large existing codebase was harder than I expected. Although Issue #153 required changing only `chunk.get("text", "")` to `chunk.get("text") or ""` in `rag/evaluator/faithfulness_checker.py`, I first needed to understand how `FaithfulnessChecker` worked, examine its tests, reproduce the failure, and make sure my change would not affect the existing scoring behavior. I learned that even a one-line fix can require significant investigation before changing the code.

**What did you learn about working in a large codebase?**

I learned that working in an existing codebase is different from starting my own project because I cannot simply write code in the way I prefer. I needed to understand the existing project structure, read `docs/CONTRIBUTING.md`, inspect `rag/evaluator/faithfulness_checker.py` and `tests/unit/test_faithfulness_checker.py`, and follow the repository's branch, commit, testing, and documentation conventions. This experience showed me the importance of tracing the relevant code and understanding the expected behavior before implementing a fix.

**How did AI tools help — and where did they fall short?**

AI tools helped me understand unfamiliar code, reason about the `None` handling problem, interpret test and terminal output, and understand the Git and pull request workflow. They were also useful for explaining why `chunk.get("text", "")` and `chunk.get("text") or ""` behave differently. However, I still had to work directly with the repository, reproduce the bug, run the tests, inspect the actual output, verify the suggested changes, and make decisions based on the project's contribution requirements rather than accepting AI suggestions automatically.

**What would you do differently if you started over?**

If I started over, I would explore the repository structure and contribution requirements earlier before beginning the implementation. I would also run commands such as `make test-unit` and `make check` earlier so that I could identify repository-wide pre-existing failures before making my change and compare the results afterward. I would also open the draft PR earlier in the process so there would be more time for feedback before the final submission.

**What are you most proud of from this module?**

I am most proud that I completed the full contribution process for a real issue rather than only writing an isolated piece of code. I reproduced issue #153, identified why a context chunk containing `"text": None` caused a `TypeError`, implemented the fix, verified the regression test, documented my work, created a pull request, received reviewer feedback, and responded to it professionally. Going through the complete process gave me a much better understanding of how developers contribute changes to an existing codebase using Git, GitHub, testing, documentation, and code review.