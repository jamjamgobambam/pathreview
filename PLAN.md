## Solution plan

**Issue:** Bias detector patterns are too narrow to match common phrasings — [#151](https://github.com/ascherj/pathreview/issues/151)

### Understand
`BiasDetector.detect_bias()` in `safety/bias_detector.py` uses hard-coded, literal-word-order regexes (no plural handling, no synonym/lemma expansion, fixed verb lists) to flag two categories of biased feedback: dismissive language about non-traditional education (lines 13-18) and demographic assumptions about age/class/immigration status (lines 21-25).

**Expected behavior:** any natural phrasing of these two bias categories — including plurals, alternate verbs ("lacks" vs "can't"), inserted nouns, and paraphrased sentence structure — should be flagged as biased.

**Actual behavior:** the regexes only match a narrow set of exact templates. Rephrasings that are semantically identical to already-covered cases (e.g. "developers" instead of "developer", "programmers" instead of "graduates/developers", "lacks" instead of "can't/won't") silently pass through as unbiased. This causes 9 of 30 tests in `tests/unit/test_bias_detector.py` to fail.

Root cause is a set of overly-specific regex literals written to match only the sentences that first came to mind, not the broader semantic pattern each was meant to capture.

### Map
- `safety/bias_detector.py:13-25` — `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` regex lists (the actual fix surface).
- `safety/bias_detector.py:38-49` — `detect_bias()` loop logic; reason strings are generic per-category labels, not tied to the specific matched pattern.
- `tests/unit/test_bias_detector.py` — 30 existing tests define the target behavior; 9 currently fail (listed below). No new tests should be needed, but may add a couple for regression coverage of the specific gaps found.
- `core/services/review_service.py:366` — `_run_safety_checks()` has only a comment placeholder for the bias check; `BiasDetector.detect_bias` isn't actually wired into the pipeline yet. Out of scope for #151 but worth flagging separately — this fix only touches the detector itself, not its integration.
- `scripts/issues_manifest.json` (`D-03`) — a related but distinct backlog item: "bootcamp" mentions being flagged as biased even when neutral/positive (false positives). Must not regress this while broadening patterns for #151.

### Plan
1. **Reproduce locally:** run `pytest tests/unit/test_bias_detector.py -v` and confirm the same 9 failing tests reported in the issue (see list below), to establish a before/after baseline.
2. **Fix `DISMISSIVE_PATTERNS` (bias_detector.py:13-18):**
   - Add `programmers?` to the noun alternation on line 15 (currently `graduates?|developers?`).
   - Loosen line 14 to not require a literal linking verb before insufficient/inadequate/lacks (support "education lacks X" as well as "education is lacks X"), and support paraphrases like "attendance means inadequate training."
   - Broaden the trigger-verb list on line 15 to include general negation ("can't write", "can't handle") in addition to "lack/missing."
   - Allow an inserted noun/plural verb in line 17 (e.g. "self-taught **developers are** not equal to...", not just "self-taught **is** not equal to...").
3. **Fix `DEMOGRAPHIC_PATTERNS` (bias_detector.py:21-25):**
   - Add optional plural `s?` to `person|developer|programmer` on line 22.
   - Generalize line 23 beyond literal `person from|coming from` to cover `developers from`, `candidates from`, `people from`, etc.
   - Add `lack` to the trigger-verb list on line 24 (currently `can't|cannot|won't|struggle`).
4. **Re-run the full test suite** (`pytest tests/unit/test_bias_detector.py -v`) and confirm all 30 tests pass, including the 9 previously failing.
5. **Regression-check against D-03:** manually verify neutral/positive bootcamp-mention test cases still return `is_biased=False`, so broadened patterns don't reintroduce the false-positive bug tracked separately in the backlog.

### Inputs & outputs
- **Input:** a single feedback text string passed to `BiasDetector.detect_bias(text)`.
- **Output:** unchanged tuple shape, `(is_biased: bool, reason: str)`. No API/signature changes — only the regex pattern lists change. Reason strings stay as the existing generic per-category labels for this fix (tying reasons to the specific matched phrase is out of scope, though it's a related idea in backlog item `D-12`).

### Risks & unknowns
- **Over-broadening risk:** loosening patterns too far could reintroduce `D-03`'s false-positive bug (flagging neutral "bootcamp" mentions). Each pattern change needs to be checked against both the failing tests it's meant to fix and the passing tests it must not break.
- **Regex complexity:** stacking more alternations/optional groups into single-line regexes reduces readability; may need to add inline comments per pattern to keep intent clear.
- **Hidden gaps in "soft-assert" tests:** `test_biased_returns_reason` and `test_unbiased_returns_empty_reason` use conditional (`if is_biased is True/False: assert ...`) guards rather than hard assertions, so they won't fail even if detection is wrong — worth tightening these assertions as part of this fix so gaps don't stay invisible to CI.
- **No integration coverage:** since `BiasDetector` isn't actually wired into `review_service.py:366` yet, this fix can't be verified end-to-end through the real feedback pipeline — only via unit tests directly against `detect_bias()`.

### Edge cases
- Plural vs. singular nouns ("developer" vs. "developers", "programmer" vs. "programmers").
- Alternate negation/trigger verbs conveying the same meaning ("can't", "won't", "lacks", "unable to").
- Inserted nouns or plural verb forms between subject and predicate ("self-taught **developers are** not equal to..." vs. "self-taught is not equal to...").
- Paraphrased sentence structure expressing the same claim without matching literal word order (e.g. "attendance means inadequate training" vs. "training is inadequate").
- Case sensitivity (already handled via `re.IGNORECASE`, should remain covered by any new patterns).
- Neutral/positive mentions of "bootcamp" or "self-taught" that must continue to return `is_biased=False` (the D-03 false-positive case).
