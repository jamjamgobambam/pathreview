## Week 7 – Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The faithfulness checker crashes when a retrieved context chunk contains `None` instead of text. The crash occurs because the checker passes the null value into `join()`, which only accepts strings. A successful fix should handle null values safely while keeping the existing behavior for valid context chunks. The affected code is located in `rag/evaluator/faithfulness_checker.py`.

**Issue-selection reasoning:**

I can explain the problem and expected behavior clearly:
- the faithfulness checker should return a score rather than crash when a context chunk contains `text: None`. 
I located the affected `check()` method in `rag/evaluator/faithfulness_checker.py` and reviewed the related test in `tests/unit/test_faithfulness_checker.py`.
This is my first open source contribution whch is why I chose this Tier 1 issue. 
I checked the issue comments and cohort ledger and am comfortable with the number of existing claims. I found no unresolved blockers or dependencies, and I estimate that the investigation, implementation, and testing can be completed before the Week 9 deadline.

**Branch name:** `fix/153-handle-none-context-text`

**Setup confirmation:** [y] App runs locally at `localhost:5173`

**Cohort ledger:** [y] Issue added to cohort ledger

## Week 8 – Reproduction & solution planning

**Reproduction commit link:** [https://github.com/dtkachepa/pathreview/tree/fix/153-handle-none-context-text]

**Reproduction summary:**

I ran the existing `test_none_context_chunk_text` test with a context chunk containing
`{"text": None}`, and it failed with the confirmed
`TypeError: sequence item 0: expected str instance, NoneType found` at the `" ".join(...)`
operation in `rag/evaluator/faithfulness_checker.py`.

Exact focused command used to reproduce it:

```
python -m pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -q
```

**PLAN.md link:** [https://github.com/dtkachepa/pathreview/blob/fix/153-handle-none-context-text/PLAN.md]

**Blockers or open questions:**
No blockers or open questions

## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed PLAN.md subtasks 1-3: implemented the null-safe context-text coercion in
`rag/evaluator/faithfulness_checker.py`, ran the existing
`test_none_context_chunk_text` regression test successfully, and ran the complete
faithfulness-checker test module. The implementation is complete and remains limited to
handling a context chunk whose `text` value is `None`.

**Next steps:**
Review the diff, commit and push the branch, open a draft PR, request and address
feedback, rerun the checks and finalize the PR.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/664

**Branch:** `fix/153-handle-none-context-text`

**What you built:**
Updated the faithfulness checker to convert missing or `None` chunk text to an
empty string before joining the retrieved context. This prevents the existing
`TypeError` while preserving valid text from the other context chunks.

**Tests added or updated:**
No test files were modified because the repository already contained
`TestFaithfulnessChecker::test_none_context_chunk_text`. The regression test
previously failed with a `TypeError` and now passes. The related
missing-text-key test also passes.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Both repository-wide commands continue to report known pre-existing failures.
The full unit result improved from 375 passed and 53 failed to 376 passed and
52 failed, and `make check` remained at the pre-change baseline of 182 lint
errors.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received.

**How you responded:**
No changes were needed because no reviewer feedback came in.

---

### Reflection

**What was harder than you expected?**
Understanding the exact scope of the bug was harder than I expected. I had to distinguish between a context chunk with `text=None` and a chunk that is itself `None`, since they would require different fixes.

**What did you learn about working in a large codebase?**
I learned that I need to understand the existing code and tests before making changes. A small fix can also be surrounded by unrelated test or lint failures, so it is important to verify what my change actually affects.

**How did AI tools help — and where did they fall short?**
AI helped me understand unfamiliar code, think through the bug, and plan my implementation. However, I still had to inspect the code, run the tests, and verify the fix myself instead of assuming the AI suggestions were correct.

**What would you do differently if you started over?**
I would reproduce the bug and inspect the relevant tests earlier before writing the full solution plan. This would make the scope of the issue clearer from the beginning.

**What are you most proud of from this module?**
I am most proud that I was able to take a real issue, understand the cause, implement a focused fix, add regression coverage, and submit a PR.