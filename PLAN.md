# PLAN.md — Issue #153

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)
**File:** `rag/evaluator/faithfulness_checker.py`
**Branch:** `fix/153-faithfulness-checker-none-text`

## 1. Reproduction

Ran the exact repro from the issue against the real file (see `scripts/repro_issue_153.py`, committed alongside this plan):

```
feedback: 'Has Python skills'
context_chunks: [{'text': None}]
Calling checker.check(feedback, context_chunks)...

REPRODUCED BUG: TypeError raised as expected -> sequence item 0: expected str instance, NoneType found
Traceback (most recent call last):
  ...
  File "rag/evaluator/faithfulness_checker.py", line 34, in check
    context_text = " ".join([
TypeError: sequence item 0: expected str instance, NoneType found
```

Confirmed this is a real bug, not a misreading of the issue: `check()` builds `context_text` with

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)` only returns `default` when `key` is **absent**. When the key exists with value `None` (as it does for chunks from documents that produced no extractable text upstream), `.get()` returns `None`, and `" ".join(...)` crashes on the first `None` item in the list.

I also confirmed the *adjacent* case already works correctly today — a chunk missing the `"text"` key entirely (e.g. `{"content": "..."}`, exercised by `test_missing_text_key_in_chunk`) does **not** crash, because there the key really is absent and the default `""` applies. That narrows the fix to the `None`-value case specifically, so I don't need to touch the missing-key path at all.

## 2. Root Cause

`chunk.get("text", "")` conflates two different situations ("key missing" vs. "key present but `None`") that need the same fallback but only one of them gets it. The fix needs to fall back to `""` in both cases.

## 3. Planned Fix

Replace the list comprehension on line 34–36 so it treats a `None` value the same as a missing key:

```python
context_text = " ".join([
    chunk.get("text") or "" for chunk in context_chunks
])
```

`chunk.get("text")` returns `None` in both the missing-key and `None`-value cases; `or ""` normalizes either to an empty string. Since chunk text should always be `str | None` in this codebase, using `or` instead of a more defensive type check keeps the fix minimal and consistent with how the rest of `faithfulness_checker.py` is written.

## 4. Files to Change

- `rag/evaluator/faithfulness_checker.py` — the one-line fix described above.
- `tests/unit/test_faithfulness_checker.py` — no new test required for the reported case (`test_none_context_chunk_text` already exists and currently fails); I'm planning to add one additional test not currently covered (see Sub-tasks #5).

No other files reference this code path (`_extract_claims` and `_is_supported` operate purely on already-built strings), so the blast radius is contained to this one file.

## 5. Sub-tasks (in order, for next week's implementation)

1. Apply the one-line fix in `faithfulness_checker.py`.
2. Run `scripts/repro_issue_153.py` again — should print a score instead of crashing.
3. Run `pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text` and confirm it now passes.
4. Run the full `tests/unit/test_faithfulness_checker.py` file to confirm no regressions, especially `test_missing_text_key_in_chunk` (the adjacent case this fix must not break).
5. Add a new test for a case not currently covered: a multi-chunk list where only *some* chunks have `text: None` (e.g. `[{"text": "Python expert"}, {"text": None}]`), to confirm the valid chunk still contributes to `context_text` and the score isn't zeroed out by one bad chunk.
6. Run `make lint`, `make format`, `make typecheck` per CONTRIBUTING.md.
7. Commit with a Conventional Commits message, e.g. `fix(rag): handle None chunk text in faithfulness checker`, body explaining the missing-key vs. None-value distinction, footer `Fixes #153`.
8. Open the PR using the repo's PR template.

## 6. Risks & Edge Cases

- **Non-string, non-None `text` values** (e.g. an int or list accidentally stored): `or ""` would also replace falsy-but-technically-present values like `0` or `[]`. Not something the issue reports and not currently possible given how chunks are constructed upstream, so I'm treating this as out of scope rather than adding type coercion nobody asked for.
- **Empty string `text` values** (`""`): unaffected — `"" or ""` still evaluates to `""`, same as before the fix.
- **All chunks are `None`**: context becomes an all-empty-string join (`""`), claims will simply score as unsupported — no crash, degrades gracefully, consistent with the "should handle gracefully" expectation in `test_none_context_chunk_text`.
- **A chunk that isn't a dict at all** (e.g. a bare string in the list): would raise `AttributeError` on `.get()`. This is a different bug from the one reported in #153 and not reproducible from the issue's steps — flagging it here so it doesn't get silently conflated with this fix, but not planning to handle it unless it comes up in review.
- **Regression risk on existing passing tests**: low. The change only affects behavior when `chunk.get("text")` is falsy; every currently-passing test in the file uses non-empty string `text` values, so none of them exercise the changed branch.

## 7. Out of Scope This Week

Per the Week 8 instructions, the actual code fix, new test, and PR are next week's work (Week 9). This week's deliverable is the reproduction (`scripts/repro_issue_153.py`) plus this plan.
