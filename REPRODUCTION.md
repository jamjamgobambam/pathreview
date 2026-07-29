# Issue #152 Reproduction

## Environment

- Branch: `fix/152-faithfulness-short-claims`
- Python: project `.venv` running Python 3.11
- Affected component: `rag/evaluator/faithfulness_checker.py`
- Date reproduced: July 27, 2026

## Direct reproduction

I ran the issue's example against the current implementation:

```bash
.venv/bin/python -c 'from rag.evaluator.faithfulness_checker import FaithfulnessChecker; f=FaithfulnessChecker(); print(f.check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}]))'
```

Observed result:

```text
0.0
```

The supporting context contains both `python` and `sql`, so the expected result is a positive faithfulness score rather than `0.0`.

Inspecting the intermediate behavior showed that `_extract_claims()` retained `Knows Python` but removed `Knows SQL` because the latter is 10 characters or shorter. The retained Python claim still scored as unsupported because `_is_supported()` found only one meaningful overlapping token (`python`) and requires at least two.

## Focused test reproduction

I ran:

```bash
.venv/bin/python -m pytest -s tests/unit/test_faithfulness_checker.py -q
```

Observed summary:

```text
4 failed, 18 passed
```

The three failures identified by issue #152 all returned `0.0`:

- `test_partial_support_returns_middle_score`
- `test_multiple_context_chunks`
- `test_multiple_claims_varying_support`

The fourth failure, `test_none_context_chunk_text`, raises a `TypeError` when a context chunk has `"text": None`. That is a separate robustness problem and should not be included in the issue #152 implementation unless the maintainer confirms that the scope should expand.

## Root-cause confirmation

`FaithfulnessChecker._is_supported()` tokenizes a claim and its context, removes stop words from their overlap, and then uses this fixed threshold:

```python
return len(meaningful_overlap) >= 2
```

Therefore, a short claim supported by one distinctive term can never pass. This local behavior matches the bug described in [issue #152](https://github.com/ascherj/pathreview/issues/152).
