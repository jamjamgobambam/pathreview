# Solution plan

**Issue:** [#153 — Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

## Understand

`FaithfulnessChecker.check()` builds one context string from retrieved chunks with:

```python
" ".join([chunk.get("text", "") for chunk in context_chunks])
```

That handles a missing `text` key, but not a present key whose value is `None`.
For `{"text": None}`, `dict.get()` returns `None`, so `" ".join(...)` raises
`TypeError: sequence item 0: expected str instance, NoneType found`.

Expected behavior: `check()` should treat `None` chunk text the same way it treats
missing text, skip that empty chunk contribution, and return a normal faithfulness
score between `0.0` and `1.0`.

Root cause: missing normalization of nullable chunk text in
`rag/evaluator/faithfulness_checker.py`.

## Map

Files involved:

- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()` concatenates
  chunk text before scoring claims.
- `tests/unit/test_faithfulness_checker.py` —
  `TestFaithfulnessChecker.test_none_context_chunk_text` is the regression test named
  in the issue.
- `JOURNAL.md` — Week 8 reproduction notes and links for the course deliverable.

Expected code touch:

- `rag/evaluator/faithfulness_checker.py`

No API, database, frontend, migration, or dependency changes are needed.

## Plan

1. Reproduce the issue from the `main` version by running:
   ```python
   from rag.evaluator.faithfulness_checker import FaithfulnessChecker
   FaithfulnessChecker().check("Knows Python.", [{"text": None}])
   ```
   Confirm it raises the `TypeError` from `" ".join(...)`.
2. In `FaithfulnessChecker.check()`, normalize each chunk text while building
   `context_text`:
   ```python
   context_text = " ".join([chunk.get("text") or "" for chunk in context_chunks])
   ```
3. Keep the existing behavior for missing `text` keys, empty context chunks, and normal
   text chunks unchanged.
4. Run the focused regression test:
   ```bash
   .venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -q
   ```
5. Before opening the PR, run the project checks required by `docs/CONTRIBUTING.md`:
   ```bash
   make check
   make test-unit
   ```

## Inputs & outputs

Function being fixed:

```python
FaithfulnessChecker.check(feedback: str, context_chunks: list[dict]) -> float
```

Input that currently fails on `main`:

```python
feedback = "Knows Python."
context_chunks = [{"text": None}]
```

Expected output after the fix:

- No exception.
- Returns a `float`.
- Score remains within `0.0 <= score <= 1.0`.
- `None` chunk text contributes no context text.

Existing happy path remains unchanged:

- `{"text": "Python portfolio content"}` is included in `context_text`.
- Missing `text` key is treated as empty text.

## Risks & unknowns

- `rag/evaluator/faithfulness_checker.py`: using `or ""` also treats other falsey values
  such as `0` or `False` as empty text. That is acceptable here because chunk text should
  be a string, and non-string values are already invalid context for text scoring.
- `tests/unit/test_faithfulness_checker.py`: the existing regression test only asserts
  that the method returns a bounded float, not an exact score. That matches the evaluator's
  current loose scoring tests, so I will not add stricter assertions unless reviewers ask.
- Full validation still depends on running `make check` and `make test-unit` before the PR,
  because the codebase uses ruff, black, mypy, and pytest per `docs/CONTRIBUTING.md`.

## Edge cases

- Context chunk has `{"text": None}`: should not crash; treat as empty text.
- Context chunk is missing `text`: should keep existing graceful behavior.
- Mixed chunks, e.g. one `None` text and one valid text string: should score against the
  valid text chunk.
- Empty `feedback` or empty `context_chunks`: should keep returning `0.0`.
