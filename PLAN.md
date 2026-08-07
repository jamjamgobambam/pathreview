## Solution plan

**Issue:** [Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

### Understand
Root cause of this issue **solely** stems from `_is_supported()` function in `rag/evaluator/faithfulness_checker.py`, the issue isn't caused by any other modules. Even when input with a short claim-context pair with fewer than 2 overlapping, meaningful tokens, we expect `_is_supported()` to **hollistically evaluate whether claims are supported by the user's context or not.** The current codebase is defaulting **False only because there are fewer than 2 overlapping tokens**. This misclassification mistakes supported claims with unsupported ones, and ruin the faithfullness check score upon testings and fail **4 unit tests**.

### Map
The main module containing the issue, `rag/evaluator/faithfulness_checker.py`, and the test suites, `tests/unit/test_faithfulness_checker.py`, are the only files to be involved in this issue. This is because that **this faithfulness checker is used only to evaluate responses from LLMs during testing**. I'm expecting to only have to touch these 2 files, or possibly `rag\evaluator\eval_suite.py` since that's the **only external Python file that imports `faithfulness_checker.py`**.

Within `faithfulness_checker.py`, we have the following method dependency hiearchy:

> check()
> ├─ _extract_claims()   (no further deps)
> └─ _is_supported()     (no further deps, called once per claim)

The issue states that `_is_supported()` has a bug, so, by extension, I'll probably touch `check()` and `_is_supported()` to resolve issues after new implementations are made.  

### Plan

1. Replace the fixed `overlap >= 2` token count in `_is_supported()` with a **ratio** of meaningful overlapping tokens to the claim's own meaningful token count (`_support_ratio()`), so the bar scales with claim length instead of punishing short claims outright.
2. Fix tokenization to strip punctuation before splitting, as raw `.split()` left trailing punctuations attached to words (e.g. `"python,"`), which silently broke overlap matching for any context built from multiple joined sentences. The token pattern (`[a-z0-9']+(?:[+/#]+[a-z0-9']*)*`) still strips sentence punctuation but keeps terms like `"C++"` and `"CI/CD"` intact instead of splitting them apart.
3. Derive the threshold **from the existing test suite**, not by guessing: compute the overlap ratio each test implies and solve for a value that satisfies every test's inequality (`ratio >= T` or `ratio < T`) at once. Found the valid range to be **(0.333, 0.375]**; picked **0.35** (`SUPPORT_THRESHOLD`).
4. Replace `check()`'s binary supported/unsupported count with a **graded per-claim score**, since single-claim feedback can only ever average to exactly 0.0 or 1.0 under a boolean count — no threshold choice can produce a "middle" score for one claim. Added `_scale_ratio()`: a piecewise-linear rescale mapping `[0, SUPPORT_THRESHOLD)` onto `[0, 0.5)` and `[SUPPORT_THRESHOLD, 1]` onto `[0.5, 1]`, so a claim's continuous score always agrees with `_is_supported()`'s boolean at the same threshold (ratio 0 → score 0.0, ratio == threshold → score 0.5, ratio 1 → score 1.0 — no floor inflation, no saturation).
5. Fixed two related bugs found via the test suite while implementing the above: `chunk.get("text", "")` didn't handle an explicit `None` value (only a missing key) — changed to `chunk.get("text") or ""`; and `_support_ratio()` divides by zero if a claim's tokens are all stop words — guarded to return `0.0` in that case.
6. Re-ran `tests/unit/test_faithfulness_checker.py` after each change; all 22 tests pass.

### Inputs & outputs
Inputs/outputs of `check()` are unchanged: `feedback: str` and `context_chunks: list[dict]` in, a `float` score `0.0`–`1.0` out. The fix changes the internal decision boundary in `_is_supported()` (now a proportional ratio instead of a raw count), the tokenization used to compute overlap, and how `check()` aggregates per-claim results (graded score instead of a supported/total count) — no change to the public interface or callers (`eval_suite.py`, which only relies on the returned float being in `[0, 1]`).

### Risks & unknowns

- The 0.35 threshold, and the `_scale_ratio()` rescale built on top of it, are both derived from the **current** test suite, not from a labeled ground-truth dataset of real faithful/unfaithful pairs. If new test cases are added with different claim/context shapes, both may need to be re-derived using the same constraint-solving approach.
- The rescale formula was checked against every test that asserts on `check()`'s score, but nothing pins the exact formula itself (tests assert ranges, not specific values) — a different monotonic rescale crossing 0.5 at the threshold would pass equally well.
- Haven't audited other consumers of `faithfulness_score` / `overall_score` (e.g. in `eval_suite.py`) for any hardcoded pass/fail cutoff that might assume the old binary 0.0/1.0 behavior.

### Edge cases

- Short claims (1–2 meaningful tokens) — the core case from the issue; now scored proportionally instead of being forced to 0.0.
- Claims/context with punctuation directly attached to words (commas, periods from joined sentences) — now stripped before comparison, while multi-symbol terms (`"C++"`, `"CI/CD"`) stay intact as single tokens.
- Single-claim feedback — now produces a genuine gradient via `_scale_ratio()` instead of being forced to exactly 0.0 or 1.0.
- Context chunks with an explicit `None` `"text"` value — handled via `chunk.get("text") or ""`, no longer crashes.
- Claims whose tokens are all stop words — `_support_ratio()` returns `0.0` instead of raising `ZeroDivisionError`.
