## Week 7 — Issue selection


***Issue link:*** https://github.com/ascherj/pathreview/issues/153
***Issue title:*** Faithfulness checker crashes when a context chunk has text: None
***Tier:*** [x] Tier 1  [ ] Tier 2  [ ] Tier 3


***Problem summary:***
The faithfulness checker component crashes when evaluating retrieved context chunks if a chunk's text field is set to `None`. When iterating through context chunks, the checker attempts string operations directly without first validating whether the text attribute contains a non-null string value. A successful fix will add defensive checks or fallback handling to handle `None` values gracefully, preventing runtime exceptions during evaluation in the RAG pipeline.


***Branch name:*** fix/153-faithfulness-checker-null-chunk-text
***Setup confirmation:*** [x] App runs locally at localhost:5173
***Cohort ledger:*** [x] Issue added to cohort ledger


## Week 8 — Issue reproduction & planning


***Reproduction steps (from issue):***
```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker
FaithfulnessChecker().check('Knows Python.', [{'text': None}])
```


***Observed locally:***
```
TypeError: sequence item 0: expected str instance, NoneType found
```
Raised from `rag/evaluator/faithfulness_checker.py:34` — `" ".join([chunk.get("text", "") for chunk in context_chunks])`.
`dict.get(key, default)` only applies the default when the key is *missing*; when `"text"` is present with value `None`, `.get()` returns `None`, and `str.join` cannot join a `None` item.


***Regression test that captures the bug:*** `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text` (already present in the suite, currently failing).


***Baseline test run (before fix):***
```
$ pytest tests/unit/test_faithfulness_checker.py -v
FAILED test_partial_support_returns_middle_score   (pre-existing, unrelated to #153)
FAILED test_multiple_context_chunks                (pre-existing, unrelated to #153)
FAILED test_multiple_claims_varying_support         (pre-existing, unrelated to #153)
FAILED test_none_context_chunk_text                 (TypeError — this is issue #153)
4 failed, 18 passed
```
The three unrelated failures are pre-existing scoring-threshold issues in `_is_supported` and are out of scope for this fix — noted here so they aren't mistaken for regressions introduced by this work.


See [PLAN.md](PLAN.md) for the fix plan.


***Fix implemented:*** `chunk.get("text", "") for chunk in context_chunks` → `chunk.get("text") or "" for chunk in context_chunks` in `rag/evaluator/faithfulness_checker.py`.


***Verification:*** `test_none_context_chunk_text` passes; full unit suite 376 passed / 52 failed vs. baseline 375 passed / 53 failed — one test flipped, no regressions. ruff/black/mypy pass via pre-commit.


***Pull Request:*** https://github.com/ascherj/pathreview/pull/339

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented the fix in `rag/evaluator/faithfulness_checker.py` so context chunks with `text: None` are treated as empty text. Verified the existing regression test now passes and confirmed the change introduces no new failures compared with the baseline.

**Next steps:** Complete the final self-review, document the verification results, and ensure pull request #339 is ready for review.

**Blockers:** The full unit suite has pre-existing, unrelated failures. Baseline: 375 passed / 53 failed; after this fix: 376 passed / 52 failed.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/339

**Branch:** `fix/153-faithfulness-checker-null-chunk-text`

**What you built:** Updated the faithfulness checker to safely handle context chunks whose `text` field is explicitly `None`. The checker now falls back to an empty string, preventing `str.join` from raising a `TypeError` while preserving behavior for valid chunks.

**Tests added or updated:** Verified `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`. The targeted regression test passes; the full suite improved from 375 passed / 53 failed to 376 passed / 52 failed, with no new failures.

**Self-review confirmation:**
- [x] `make check` passes for the changed code (no new failures)
- [x] `make test-unit` introduces no new failures relative to baseline

**Draft PR feedback received from:** none
