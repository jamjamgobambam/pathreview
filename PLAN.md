## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported — https://github.com/ascherj/pathreview/issues/152

### Understand

**Root cause:** In `FaithfulnessChecker._is_supported()` (`rag/evaluator/faithfulness_checker.py`), a claim is marked supported only when at least **two** non-stopword tokens overlap with the context. Short factual claims such as `Knows Python` share a single meaningful token (`python`) with a fully supporting context (`python expert`), so they are always scored unsupported.

**Expected:** Feedback made of short, fully grounded claims should score near `1.0` (each claim supported).

**Actual (pre-fix):**
```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker
f = FaithfulnessChecker()
f.check('Knows Python. Knows SQL.', [{'text': 'python expert'}, {'text': 'sql expert'}])
# → 0.0
```
Only `Knows Python` was extracted (`Knows SQL` failed the `len > 10` claim filter). Meaningful overlap was `{'python'}` (length 1), so `_is_supported` returned `False` and the score collapsed to `0.0`.

Related unit tests that fail for the same reason: `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support` in `tests/unit/test_faithfulness_checker.py`.

### Map

| File | Role |
|------|------|
| `rag/evaluator/faithfulness_checker.py` | Bug location: `_extract_claims`, `_is_supported`, and `check` |
| `tests/unit/test_faithfulness_checker.py` | Spec via failing/related unit tests; regressions after the fix |
| `rag/evaluator/eval_suite.py` | Caller that aggregates faithfulness into overall eval score (read-only unless API changes) |

**Functions to change:** `_extract_claims`, `_is_supported` (and likely a new graded `_support_score` / tokenization helper). **`check`** should average per-claim support instead of a hard 0/1 ratio when partial evidence matters.

### Plan

1. **Normalize tokenization** — Replace naive `.split()` with punctuation-aware token extraction so `Python,` matches `python`, and treat `chunk.get("text") or ""` so `text: None` does not crash context aggregation.
2. **Allow one-token support only for short reporting claims** — Keep the existing two-token floor for multi-token material claims (`Python expert`, `Skilled with Docker`). Add a narrow exception for bare one-token claims and `Knows <fact>` / `[The] candidate knows <fact>` forms so issue #152’s examples can pass without loosening every claim.
3. **Grade partial support** — When a longer claim shares some but not enough tokens, return a capped partial score (below the support threshold, e.g. ≤ 0.4) so middle-score tests stay valid instead of collapsing to `0.0` or `1.0`.
4. **Fix short-claim extraction** — Stop dropping scoreable fragments solely because `len(text) <= 10`, so `Knows SQL` and similar short sentences are included.
5. **Verify** — Re-run the issue reproduction (expect `1.0`), then `pytest tests/unit/test_faithfulness_checker.py`, and confirm the three previously failing tests pass without regressing full-support / no-support cases.

### Inputs & outputs

**Inputs:**
- `feedback: str` — generated review text (may include short `Knows X` sentences)
- `context_chunks: list[dict]` — retrieved chunks with a `text` field (possibly missing or `None`)

**Outputs / behavior change:**
- `check(...)` returns a float in `[0.0, 1.0]` that is the mean per-claim support score
- Short grounded claims contribute ~1.0 support instead of always 0.0
- Longer claims still need ≥2 overlapping meaningful tokens (or graded partial credit if not fully supported)
- `_is_supported(claim, context)` remains a boolean API for existing unit tests (`score >= 0.5`)

### Risks & unknowns

- **Over-loosening the threshold:** Changing every claim to “≥1 token overlap” would make `Python expert` pass on context that only mentions `Python`. Mitigation: gate the one-token rule to bare / `Knows`-form claims only; keep investigating `_is_supported` call sites in `tests/unit/test_faithfulness_checker.py`.
- **Claim extraction side effects:** Removing the `len > 10` filter may admit noise fragments. Mitigation: require that a fragment tokenizes to at least one token before counting it as a claim.
- **Partial-score calibration:** The middle-range tests expect `0.2 < score < 0.8`. A bad cap (e.g. partial = 0.1) could still fail `test_partial_support_returns_middle_score`. Mitigation: tune partial ceiling just below the support threshold and re-run that test while iterating.
- **Lexical limits remain:** This checker is bag-of-tokens overlap, not NLI. Negated context (`No Python knowledge`) can still look supported for a one-token `Knows Python` claim — accept as an explicit tradeoff for #152, document in comments if needed.

### Edge cases

- Short claims: `Knows Python.`, `Knows SQL.`, `The candidate knows Python.`
- Punctuation-attached tokens: `Python,` / `JavaScript,` in multi-skill sentences (`test_multiple_context_chunks`)
- Mixed support across multiple short sentences (`Python expert. Knows Rust. Skilled with Docker.`)
- Empty feedback, empty chunks, missing `text` key, and `text: None`
- Longer fully supported and fully unsupported feedback (must not flip those existing assertions)
- Case-insensitive matching (`PYTHON` vs `python`)
- Technical compounds if present in feedback/context (`Node.js`, `C++`, `C#`) — tokenize without splitting them into unsafe single letters
