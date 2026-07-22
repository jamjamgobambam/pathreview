# PLAN.md — Issue #151: Broaden bias detector patterns

**Issue:** Bias detector patterns are too narrow to match common phrasings
**File:** `safety/bias_detector.py` (+ `tests/unit/test_bias_detector.py`)
**Branch:** `fix/151-bias-detector-patterns`
**Tier:** 1

---

## 1. Problem & root cause

`BiasDetector.detect_bias()` matches text against a handful of rigid regexes
(`DISMISSIVE_PATTERNS`, `DEMOGRAPHIC_PATTERNS`). Each regex requires an almost
exact word sequence with fixed adjacency, so any real-world paraphrase slips
through as a **false negative**. Reproduced: 8/8 clearly biased statements
returned `(False, '')`, e.g.:

```
BiasDetector.detect_bias("Bootcamp grads just aren't as capable as real CS majors.")
# -> (False, '')   # should be True
```

Root causes:
- **Adjacency-locked** — inserted words ("you probably don't have the
  fundamentals") break the match.
- **Tiny vocabulary** — only `lack/insufficient/inadequate` etc.; misses
  "aren't as capable", "won't cut it", "too old to".
- **Missing categories** — no gender bias patterns at all; background list is
  limited to `poor/rich/working-class`.

## 2. Design tension (do NOT regress)

There is a competing failure mode (false positives): the detector must still
**not** flag neutral/positive mentions such as
`"your bootcamp background shows strong fundamentals"`. The existing tests
`test_positive_bootcamp_mention_not_flagged` /
`test_neutral_bootcamp_mention_not_flagged` /
`test_comparative_without_bias` must stay green. Broadening cannot become
"flag any text containing 'bootcamp'".

## 3. Approach: subject + dismissive-predicate co-occurrence

Replace brittle full-sentence templates with a **two-signal, proximity-based**
match. Flag text only when a *demographic/background subject* term co-occurs
near a *dismissive/negative predicate* term. This catches paraphrases (any
subject × any predicate) while staying specific — a positive predicate
("strong", "solid", "shows") next to the same subject is not flagged.

Concretely, per bias category define two vocab groups and match when both
appear within a small word window (e.g. within ~8 tokens / same clause):

- **Education subjects:** `bootcamp`, `coding bootcamp`, `self-taught`,
  `online course`, `non-traditional background`, `no CS degree`
- **Demographic subjects:** age (`young`, `old`, `too old`, `aged`, `her age`),
  origin (`immigrant`, `international`, `foreign`, `from a poor/working-class
  background`), gender (`women`, `female developers`, `she`) — **new category**
- **Dismissive predicates:** `lack(s)`, `missing`, `insufficient`, `inadequate`,
  `not (as) capable`, `can't / cannot / won't / will not`, `struggle`,
  `not equal/comparable`, `less suited`, `won't cut it`, `not ready`,
  `too demanding`, `can't keep up`, `hard time`

Implementation options (decide during build):
- **(A) Proximity regex** — build patterns programmatically as
  `subject … {0,N words} … predicate` and the reverse order. Keeps the pure-regex, dependency-free style already in the file. **Preferred** for a Tier-1 change.
- (B) Token-window scan — split into clauses, check subject-set ∩ predicate-set co-occurrence. More readable, slightly more code. Fallback if regex proximity gets unwieldy.

Return value/shape stays identical: `tuple[bool, str]` with a per-category
reason string, so no callers change.

## 4. Concrete changes

1. Restructure the pattern data as `{category: {"subjects": [...],
   "predicates": [...], "reason": "..."}}`.
2. Add a helper that compiles subject×predicate proximity patterns (both word orders) once at class load.
3. Add the **gender** category and expand age/background/education vocab per §3.
4. Keep a small allow-list guard: if the nearby predicate is clearly positive
   (`strong`, `solid`, `shows`, `good`, `both have value`), do not flag — protects
   the existing positive/neutral tests.
5. Preserve `logger.warning("bias_detected", reason=...)` behavior.

## 5. Test plan

- **Add** a parametrized `test_common_biased_phrasings_detected` covering the 8 reproduction phrasings (currently red → green after fix).
- **Add** a gender-bias detection test (new category).
- **Keep** all existing positive/neutral/clean tests green (false-positive
  guard). Explicitly re-run:
  `test_positive_bootcamp_mention_not_flagged`,
  `test_neutral_bootcamp_mention_not_flagged`,
  `test_comparative_without_bias`,
  `test_clean_feedback_not_flagged`.
- **Add** a couple of near-miss negatives to pin the boundary, e.g.
  `"Your bootcamp project is strong but lacks tests"` should **not** be flagged
  (predicate refers to the project, not the person's background).
- Run: `make test-unit` (or `.venv/bin/pytest tests/unit/test_bias_detector.py -v`).

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Over-broad → false positives (regresses D-03 concern) | Positive-predicate allow-list + proximity window + keep existing negative tests |
| Proximity window too large catches unrelated clauses | Constrain window to ~8 tokens / stop at sentence boundary |
| Regex complexity hard to maintain | Generate patterns from vocab lists in code, not hand-written strings |

## 7. Out of scope

- ML/LLM-based bias classification (tracked separately, higher tier).
- Offline bias audit report (separate issue, `scripts/audit_bias.py`).
- Wiring detector into the review pipeline (currently `detect_bias` has no
  callers; not part of this fix).

## 8. Steps / checklist

- [ ] Restructure pattern data into subject/predicate/reason groups
- [ ] Add proximity-match helper (approach A)
- [ ] Expand vocab + add gender category
- [ ] Add positive-predicate allow-list guard
- [ ] Add failing repro test, confirm it fails on `main` state
- [ ] Implement fix, confirm new + existing tests pass
- [ ] `make check` (lint/format/typecheck) clean
- [ ] Open PR against `ascherj/pathreview`, link issue #151
