

## Week 9 — Implementation and PR

### Check-in 1 — Implementation Progress

**Current progress**

I implemented the fix for Issue #153. The faithfulness checker previously
crashed when a retrieved context chunk contained an explicit `text: None`
value because `str.join()` received a `None` value.

I updated `rag/evaluator/faithfulness_checker.py` so missing or `None` text
values are normalized to an empty string. Valid text from other context chunks
is preserved.

I also updated `tests/unit/test_faithfulness_checker.py` with regression
coverage for:

- A context chunk containing `{"text": None}`
- A context chunk with a missing `text` key
- Mixed valid and `None` context chunks

**Next steps**

- Run the targeted regression tests
- Compare the complete unit suite against upstream `main`
- Complete the pull request description
- Perform the final submission review

**Blockers**

The complete repository test suite contains unrelated baseline failures. I
compared the feature branch against upstream `main` and documented the results
in Check-in 2.

### Check-in 2 — Final Submission

**Pull request**

https://github.com/ascherj/pathreview/pull/741

**Working branch**

`fix/153-handle-none-context-text`

**Branch URL**

https://github.com/anshbabar/pathreview/tree/fix/153-handle-none-context-text

**What I implemented**

Updated the faithfulness checker so context chunks containing `text: None` are
treated as empty text instead of causing `" ".join(...)` to raise a
`TypeError`. Valid context from other chunks remains available to the checker.

**Tests created or modified**

Test file:

`tests/unit/test_faithfulness_checker.py`

Coverage:

- `test_none_context_chunk_text` verifies that explicit `None` text does not
  crash the checker.
- `test_missing_text_key_in_chunk` verifies that a missing `text` key is
  handled.
- `test_none_context_chunk_preserves_valid_context` verifies that a `None`
  chunk does not discard valid context from another chunk.

**Testing results**

Targeted Issue #153 tests:

- 3 passed
- 0 failed

Complete unit-suite comparison:

- Upstream `main`: 53 failed, 375 passed
- Feature branch: 52 failed, 377 passed

The branch adds one regression test and fixes the existing
`test_none_context_chunk_text` failure. It introduces no new failures relative
to upstream `main`.

Manual verification confirmed that passing `[{"text": None}]` returns a float
without raising a `TypeError`.

**Self-review checklist**

- [x] Working branch name and URL recorded
- [x] Pull request link recorded
- [x] Pull request template completed
- [x] Implementation is limited to Issue #153
- [x] Targeted regression tests pass
- [x] Test file and coverage documented
- [x] Branch compared against upstream `main`
- [x] No new unit-test failures introduced
- [x] Ruff passes on the changed Python files
- [x] Black passes on the changed Python files
- [ ] `make check` passes repository-wide — unrelated baseline errors remain
- [ ] `make test-unit` passes repository-wide — baseline failures documented

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided during Summer 2026. My PR is still available for review, but I did not receive any comments requiring additional changes during this module.

**How you responded:**
No changes were required in response to reviewer feedback.

---

### Reflection

**What was harder than you expected?**

The hardest part was determining whether failing tests were caused by my implementation or were already existing failures in the PathReview codebase. My change for Issue #153 was relatively small, but validating it safely required understanding the surrounding faithfulness-checking logic and the project's testing setup. When I initially ran the broader test suite, I saw many failures, so I had to compare the results from the upstream main branch with my feature branch rather than assuming that every failing test was caused by my code. This made testing and validation more involved than I originally expected.

**What did you learn about working in a large codebase?**

I learned that making a small change in a large codebase requires much more context than implementing the same functionality in a personal project. For Issue #153, the visible problem was that the faithfulness checker could crash when a context chunk contained `text: None`, but I still needed to understand where that value flowed through the system, how the existing code expected context chunks to behave, and which tests were relevant. I also learned the importance of minimizing the scope of a change. Instead of redesigning unrelated parts of the checker, I focused on handling the `None` case and adding regression coverage for that specific behavior.

**How did AI tools help — and where did they fall short?**

AI tools were most helpful for understanding unfamiliar sections of the codebase, interpreting test failures, reviewing possible implementations, and reasoning through Git and pull request workflows. They helped me narrow down where the `None` value needed to be handled and think through edge cases. However, AI could not replace actually running the repository's tests and examining the results. In particular, when the full test suite contained failures, I needed to compare the behavior of my branch against the upstream main branch to determine whether my change introduced regressions. The repository itself, its test output, and Git history were ultimately the source of truth.

**What would you do differently if you started over?**

If I started over, I would establish a baseline test result from the upstream main branch before making any implementation changes. That would have made it much easier to distinguish existing repository failures from failures introduced by my branch. I would also spend more time at the beginning tracing the affected execution path and identifying the smallest relevant test set before modifying the code. This would make the development and verification process more systematic and reduce time spent debugging unrelated failures.

**What are you most proud of from this module?**

I am most proud of learning how to approach an existing codebase like a contributor rather than treating it like one of my own projects. I took a real issue, reproduced and investigated the behavior, implemented a focused fix, added regression coverage for the `None` context case, tested the change, and submitted it through the pull request workflow. More importantly, I learned how to verify that my implementation improved the targeted behavior without assuming that unrelated failures in a large repository were caused by my changes.