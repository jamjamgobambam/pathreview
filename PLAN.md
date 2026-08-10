# PathReview Issue #152

## Solution plan

**Issue:** [#152 — Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

### Understand

`FaithfulnessChecker.check()` estimates whether feedback is grounded in retrieved context. It extracts sentence-like claims with `_extract_claims()`, concatenates the text from every context chunk, asks `_is_supported()` for a Boolean decision on each claim, and returns the number of supported claims divided by the number of extracted claims.

The immediate root cause is the fixed rule in `FaithfulnessChecker._is_supported()` that requires at least two overlapping non-stopword tokens. A short factual claim can be fully supported by one distinctive term—for example, `Knows Python` and `python expert` share only `python`—but the current rule always rejects it. Locally, the issue example returned `0.0`, and the three tests named in the issue also returned `0.0`.

There is a second behavior to investigate before implementing the fix: `_extract_claims()` discards text whose stripped length is 10 characters or fewer, so `Knows SQL` and `Knows Rust` may be removed before support is checked. The correct implementation should recognize short, specific evidence and produce partial scores for mixed support without treating a generic one-word overlap as proof. Simply lowering the fixed threshold from two tokens to one may create false positives and may still fail the existing partial-support expectations.

### Map

Files and functions likely involved:

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker.check()` calculates the final supported-claim ratio.
  - `FaithfulnessChecker._extract_claims()` determines which short statements reach the scorer and may need its length rule adjusted.
  - `FaithfulnessChecker._is_supported()` tokenizes text, filters stop words, and applies the fixed two-token threshold.
- `tests/unit/test_faithfulness_checker.py`
  - Add focused regression coverage for supported and unsupported short claims.
  - Update or clarify `test_minimum_overlap_required`, whose current comment describes the behavior that issue #152 says is incorrect.
  - Use the existing partial-support, multiple-context, and mixed-claim tests to validate scoring behavior.
- `REPRODUCTION.md`
  - Keep the observed failure as the baseline against which the Week 9 implementation will be checked.

No API routes, database models, frontend components, or migrations are expected to change.

### Plan

1. Add narrowly focused regression tests in `tests/unit/test_faithfulness_checker.py` before changing production code. Cover a supported short claim with one distinctive overlap, an unsupported short claim with no overlap, and the issue's multiple-claim example so the intended score is explicit.
2. Characterize claim extraction with direct tests for `Knows Python`, `Knows SQL`, and `Knows Rust`. Decide whether to remove or replace `_extract_claims()`'s `len(...) > 10` filter so legitimate short facts are retained without treating punctuation-only fragments as claims.
3. Refine token normalization and support calculation in `rag/evaluator/faithfulness_checker.py`. Normalize punctuation consistently, exclude stop words and any clearly generic vocabulary, and use a short-claim-aware rule rather than the unconditional `len(meaningful_overlap) >= 2` threshold.
4. Preserve partial scoring for compound or mixed feedback. Determine whether coordinated facts should be extracted as separate claims or whether `check()` needs a graded per-claim support value; choose the smallest approach that makes the three issue-linked tests pass without turning partially supported feedback into `1.0`.
5. Run `pytest tests/unit/test_faithfulness_checker.py -v`, then `make test-unit` and `make check`. Compare the fixed direct reproduction with `REPRODUCTION.md` and confirm unrelated unsupported-claim and stop-word tests still pass.

### Inputs & outputs

Primary public behavior:

```python
FaithfulnessChecker.check(
    feedback: str,
    context_chunks: list[dict],
) -> float
```

- `feedback` is generated review feedback containing one or more textual claims.
- `context_chunks` contains retrieved evidence; each expected chunk has a string value under `"text"`.
- The output remains a deterministic `float` from `0.0` to `1.0`.
- Empty feedback or an empty context list should continue to return `0.0`.
- A fully supported set of short claims should produce a high score rather than `0.0`.
- A mixture of supported and unsupported claims should produce a score strictly between `0.0` and `1.0`.
- Feedback with no meaningful support should remain near `0.0`.

Internal behavior may change in `_extract_claims()` and `_is_supported()`, but their inputs remain strings. If a graded helper is introduced, it should return a bounded support value that `check()` can aggregate without changing the public method signature.

### Risks & unknowns

- **False positives in `_is_supported()`:** Accepting every single shared word could mark claims as supported because of generic terms such as `developer`, `skills`, or `experience`. Regression tests must distinguish a specific technology overlap from generic vocabulary.
- **Claim boundaries in `_extract_claims()`:** Sentence-only splitting treats `Python expertise and Kubernetes knowledge` as one claim even though only one fact is supported. I need to determine whether limited conjunction/list splitting is safe or whether graded scoring inside `check()` is less brittle.
- **Short-claim length filter in `_extract_claims()`:** Removing `len(s.strip()) > 10` may admit fragments, while retaining it drops valid claims such as `Knows SQL`. The investigation path is to add direct extraction tests and inspect other callers for assumptions about minimum claim length.
- **Token normalization in `_is_supported()`:** The current use of `.split()` leaves punctuation attached, so `Python,` and `Python` may not match. Any normalization change must preserve case-insensitive behavior and technical tokens such as `C++`, `CI/CD`, and `PostgreSQL`.
- **Existing test intent:** `test_minimum_overlap_required` documents the old two-token rule but has no truth-value assertion. The test should be clarified rather than silently preserved as authority over issue #152.
- **Separate `None` context bug in `check()`:** `test_none_context_chunk_text` raises a `TypeError` during `" ".join(...)`. That failure should be tracked separately unless the maintainer confirms it belongs in #152, so this fix does not grow beyond the selected issue.

### Edge cases

- `Knows Python` with context `python expert`: one distinctive overlap should count as support.
- `Knows Rust` with context `python expert`: no meaningful overlap should remain unsupported.
- `The candidate is experienced` with context `the candidate is available`: overlap consisting only of stop words or generic words should not count as support.
- `Knows Python. Knows Rust. Skilled with Docker.` with Python and Docker context: the result should be between `0.0` and `1.0`, reflecting two supported claims and one unsupported claim.
- `Python expertise and Kubernetes knowledge` with only Python evidence: partial support should not become either `0.0` or `1.0`.
- `Python, JavaScript, and Docker experience` supported across three separate context chunks: evidence from all chunks should contribute.
- The same keyword with punctuation or casing differences, such as `PYTHON`, `Python,`, and `python`, should match after normalization.
- Empty feedback, empty context, a missing `"text"` key, and `"text": None` should be handled without creating an out-of-range score; the `None` case may require a separate issue if it remains outside #152.
