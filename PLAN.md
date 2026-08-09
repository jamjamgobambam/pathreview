## Solution plan

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings #151

### Understand

The regex patterns in `bias_detector.py` use deterministic word-by-word matching (e.g. `self-taught|online\s+course`) to detect feedback that dismisses a portfolio based on non-traditional education, demographics, or background. Other bias signals include college prestige, internship experience, project maturity, age, and socioeconomic background.

Example reproduction:

```python
from safety.bias_detector import BiasDetector

BiasDetector.detect_bias(
    "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education"
)
# Before fix: (False, '')
# After fix:  (True, 'Dismissive language about educational background')
```

Nine unit tests in `tests/unit/test_bias_detector.py` specified the intended coverage but failed because patterns required near-exact phrase order.

### Map

Scope is limited to `safety/bias_detector.py` — the `BiasDetector` class only. No other files consume `BiasDetector` in production yet (`_run_safety_checks` in `review_service.py` is still a placeholder).

### Plan

- [x] **Step 0** — Branch setup: `fix/151-fix-bias-detection`
- [x] **Step 1** — Add reusable regex fragments (`_EDU_SOURCE`, `_ROLE`, `_DISMISSAL_VERB`, `_DEMOGRAPHIC_ROLE`, `_SOCIOECONOMIC_BACKGROUND`)
- [x] **Step 2** — Broaden `DISMISSIVE_PATTERNS` to catch natural phrasing variations
- [x] **Step 3** — Broaden `DEMOGRAPHIC_PATTERNS` for plural roles and socioeconomic backgrounds
- [x] **Step 4** — Verify all 32 existing tests pass (9 previously failing + 23 regression guards)
- [x] **Step 5** — Add test for issue reproduction example (`test_bootcamp_formal_cs_comparison_detected`)
- [x] **Step 6** — Confirm positive/neutral bootcamp mentions still pass
- [ ] **Step 7** — Submit PR

#### Decision: regex only, no LLM

Evaluated using an open language model vs. expanding regex. Chose regex because:

- Matches existing safety module conventions (`content_filter.py`, `prompt_defense.py`)
- Deterministic — unit tests can assert exact behavior
- Zero latency/cost; Tier 1 scope
- The 9 failing tests define the contract for this layer

An LLM skill would be a separate, larger change and is out of scope for #151.

#### No new bias categories needed

Existing categories cover all failing tests:

- **Dismissive language about educational background** — bootcamp, self-taught, online course dismissals
- **Demographic assumptions detected** — age, socioeconomic background, immigrant/international assumptions

### Inputs & outputs

**Input:** Feedback text string passed to `BiasDetector.detect_bias(text)`.

**Output:** `tuple[bool, str]` — `(True, reason)` if biased language detected; `(False, "")` otherwise.

**Changes made:**

| Gap | Example phrasing | Fix |
|---|---|---|
| Missing dismissal verbs | `"bootcamp graduates can't write production code"` | `_DISMISSAL_VERB` fragment with `can't`, `lacks`, etc. |
| Required exact `is` before `lacks` | `"bootcamp education lacks fundamentals"` | Made `is` optional |
| Singular-only role nouns | `"young developers can't..."`, `"bootcamp programmers lack..."` | `_ROLE` / `_DEMOGRAPHIC_ROLE` with plural forms |
| Missing `coding bootcamp` prefix | `"coding bootcamp graduates can't..."` | `_EDU_SOURCE` with optional `coding` prefix |
| Subject-verb variation | `"self-taught developers are not equal to..."` | Optional role + `is\|are` |
| Narrow socioeconomic pattern | `"developers from poor backgrounds can't..."` | Broadened `from` + background pattern |
| Causal assumption phrasing | `"bootcamp attendance means inadequate training"` | New `means inadequate` pattern |
| Formal CS comparison | Issue reproduction example | New bootcamp + formal CS rigor patterns |

**Expected outcome:** `pytest tests/unit/test_bias_detector.py` — **33 passed, 0 failed** ✓

### Risks & unknowns

| Risk | Resolution |
|---|---|
| LLM vs regex | Decided regex is sufficient for this issue's scope |
| Over-broad patterns causing false positives | All 23 previously passing negative tests still pass |
| Subjective "fit" judgments | Out of scope — e.g. `"bootcamp experience is good but does not fit our company"` correctly not flagged |
| Implicit/semantic bias | Not solvable at regex layer; documented as limitation for PR |

**Known limitations (document in PR):**

- Regex only catches phrasings matching known patterns — not implicit bias
- Issue mentions `"Given their age, they likely cannot keep up with modern frameworks"` but no test in the suite expects this phrasing
- `BiasDetector` is not wired into production safety checks yet

### Edge cases

| Input | Expected | Test coverage |
|---|---|---|
| Positive bootcamp mention | Not flagged | `test_positive_bootcamp_mention_not_flagged` |
| Neutral bootcamp mention | Not flagged | `test_neutral_bootcamp_mention_not_flagged` |
| Balanced comparison ("Both have value") | Not flagged | `test_comparative_without_bias` |
| Factual observation ("resume shows bootcamp attendance") | Not flagged | `test_assumption_vs_observation` |
| Subjective fit without dismissal | Not flagged | No dedicated test; acceptable out-of-scope |

### Pre-existing failures (baseline)

Documented before and after changes — this PR introduces no new failures:

| Command | Baseline | After changes |
|---|---|---|
| `make test-unit` (bias tests) | 9 failed, 23 passed | **33 passed, 0 failed** |
| `make test-unit` (repo-wide) | ~52 failed, ~345 passed | ~43 failed, ~355 passed |
| `make check` | 182 lint errors repo-wide | 182 lint errors (no new errors in touched files) |
