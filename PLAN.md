# Solution plan

**Issue:** [Implement a red-teaming test suite for the prompt injection defense](https://github.com/ascherj/pathreview/issues/71)

### Understand

**Root cause:** Issue #71 is a feature gap plus a coverage gap. `safety/prompt_defense.py` only matches a small set of regex patterns (separators, role labels, template delimiters, “Ignore/Forget/…”, and `execute|run|eval(`). Unit tests in `tests/unit/test_prompt_defense.py` only exercise those same patterns. There is no curated attack corpus, no `tests/security/test_prompt_injection.py`, and CI (`.github/workflows/ci.yml`) never runs `-m security` — so PRs that touch `safety/` are not gated by a red-team suite.

**Expected vs actual:**
- **Expected:** A fixture corpus under `tests/fixtures/injection_attempts/` plus a security-marked suite that attempts known injections and asserts every one is blocked; CI runs that suite when `safety/` changes.
- **Actual (reproduced):** Both paths are missing. Probing `PromptDefense.is_injection_attempt` with common jailbreak / encoding / XML-tag payloads shows multiple misses (`dan_jailbreak`, `base64_instruction`, `translate_then_ignore`, `developer_mode`, `xml_tag_injection`). Documented in `tests/security/test_prompt_injection_reproduction.py` (7 failing tests).

### Map

| Area | Path | Role |
|---|---|---|
| Defense under test | `safety/prompt_defense.py` (`PromptDefense.is_injection_attempt`, `sanitize`, `INJECTION_PATTERNS`) | Likely extend patterns / detection logic so curated attacks are blocked |
| Existing unit coverage | `tests/unit/test_prompt_defense.py` | Keep as fast pattern-level unit tests; do not replace with the red-team suite |
| Missing suite (create) | `tests/security/test_prompt_injection.py` | Red-team entrypoint named in #71 |
| Missing fixtures (create) | `tests/fixtures/injection_attempts/` | Curated payloads (one file or JSON index per attack family) |
| Reproduction (Week 8) | `tests/security/test_prompt_injection_reproduction.py` | Failing evidence; retire or fold into real suite in Week 9 |
| Pytest marker | `pyproject.toml` (`security` marker already defined) | Already available |
| CI gating | `.github/workflows/ci.yml` | Add a job (or step) that runs security tests when `safety/**` changes |

**Files we expect to modify/add in Week 9:**
1. `tests/fixtures/injection_attempts/` (new corpus)
2. `tests/security/test_prompt_injection.py` (new suite)
3. `safety/prompt_defense.py` (extend detection so corpus passes)
4. `.github/workflows/ci.yml` (run `-m security` on `safety/` PRs)
5. Remove or slim `tests/security/test_prompt_injection_reproduction.py` once the real suite lands

### Plan

1. **Build the fixture corpus** — Add `tests/fixtures/injection_attempts/` with a stable set of payloads (jailbreaks, role/delimiter escapes, template/XML tags, encoding tricks, benign controls). Prefer a small JSON/YAML index plus `.txt` payloads so cases are reviewable.
2. **Implement `tests/security/test_prompt_injection.py`** — Load fixtures, assert `is_injection_attempt` is `True` for attacks and `False` for benign controls; mark with `@pytest.mark.security`. Optionally assert `sanitize` strips dangerous delimiters where relevant.
3. **Harden `PromptDefense`** — Extend `INJECTION_PATTERNS` / detection carefully so every curated attack is blocked without flagging normal resume/portfolio text (reuse clean cases from unit tests + new benign fixtures).
4. **Wire CI** — Update `.github/workflows/ci.yml` so PRs that touch `safety/` (path filter) run `pytest -m security`.
5. **Cleanup & verify** — Replace reproduction failures with the real suite, run unit + security locally, and document residual blind spots in the PR.

### Inputs & outputs

**Inputs:** Curated injection strings (and benign controls) from `tests/fixtures/injection_attempts/`; `PromptDefense` API.

**Outputs / changes:**
- New security test suite that fails CI if any curated attack is missed
- Stronger `PromptDefense` detection covering the corpus
- CI path that executes `-m security` when `safety/` changes
- No change to product API contracts; safety behavior becomes stricter on malicious input only

### Risks & unknowns

- **False positives:** Broader patterns (e.g. matching the word “ignore” anywhere) could flag legitimate resume text — mitigate with anchored/multiline-aware patterns and a benign fixture set.
- **Encoding / obfuscation:** Base64 and “translate then …” attacks may need more than regex; decide whether Week 9 scope is regex-only expansion vs. light normalization (decode/strip tags) — investigate in `prompt_defense.py` before over-scoping.
- **CI noise:** Running security on every PR vs. path-filtered to `safety/**` — prefer path filter to match #71 wording (“every PR that touches `safety/`”).
- **Overlap with unit tests:** Avoid duplicating every unit case in the red-team suite; keep unit tests for individual patterns and security suite for adversarial corpus coverage.

### Edge cases

- Benign text containing words like “ignore”, “system”, or code snippets in a README/resume
- Multilingual or spaced/obfuscated variants of “Ignore previous instructions”
- Empty / whitespace-only input
- Very long pasted resumes with many newlines (performance + false separator matches)
- Payloads that are only malicious *after* sanitize strips `{`/`}`/`<>` (order of sanitize vs detect)
- Attacks already blocked today (delimiter `---`, `\nForget …`) must keep passing — no regressions
