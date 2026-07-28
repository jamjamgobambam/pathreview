## Solution plan

**Issue:** [Implement a red-teaming test suite for the prompt injection defense (#71)](https://github.com/ascherj/pathreview/issues/71)

### Understand

**Root cause / gap.** PathReview ships a prompt-injection defense
(`safety/prompt_defense.py`, class `PromptDefense`) but has **no automated,
regression-proof evidence that it works**. Concretely:

- The `security` pytest marker is declared in `pyproject.toml` but matches
  **0 tests** (`pytest -m security` → "no tests collected (428 deselected)").
- `tests/security/` contains only `__init__.py`.
- There is no `test-security` job in `.github/workflows/ci.yml`, so nothing
  runs the defense on every commit.

**Expected vs. actual.** *Expected:* a curated set of known injection payloads
is fed through the safety layer and every one is asserted blocked, running
automatically in CI whenever `safety/` changes. *Actual:* no such suite exists,
and reproduction revealed the defense also has a real bypass — every regex in
`INJECTION_PATTERNS` is anchored to a leading newline (`\n`), so a first-line
attack ("Ignore all previous instructions…", "System: …") with no preceding
newline is **not** detected (see `tests/security/test_injection_reproduction.py`).

This means the suite cannot simply assert "all blocked" against today's code —
part of the work is deciding how to represent known gaps vs. hardening the
defense so the suite is honestly green.

### Map

Files I expect to touch or add:

- **`safety/prompt_defense.py`** — harden `INJECTION_PATTERNS` so first-line
  (non-newline-prefixed) attacks are caught; keep false positives low.
- **`tests/security/test_prompt_injection.py`** *(new)* — the red-team suite:
  parametrized over the fixture payloads, asserting each is blocked, marked
  `@pytest.mark.security`.
- **`tests/security/conftest.py`** *(new)* — fixture loader that reads the
  payload files and exposes them to the suite.
- **`tests/fixtures/injection_attempts/`** *(new)* — payloads grouped by attack
  category (e.g. `role_switching.txt`, `instruction_override.txt`,
  `template_injection.txt`, `code_execution.txt`, `separator.txt`), one attack
  per line; plus a `benign.txt` control set for false-positive checks.
- **`.github/workflows/ci.yml`** — add a `test-security` job that runs
  `pytest -m security` (or `pytest tests/security`) with `LLM_PROVIDER=mock`,
  triggered on changes under `safety/`.
- **`tests/security/test_injection_reproduction.py`** — fold/retire this
  reproduction file into the real suite once the defense is hardened.
- Reference only (no change expected): `tests/unit/test_prompt_defense.py`,
  `pyproject.toml` (marker already present).

### Plan

1. **Curate payload fixtures.** Create `tests/fixtures/injection_attempts/`
   with category files covering role-switching, instruction override
   (ignore/forget/disregard/override), template/Jinja injection, code
   execution, and separator-line attacks — including first-line and
   mixed-case variants. Add a `benign.txt` control set.
2. **Build the suite.** Add `tests/security/conftest.py` to load fixtures and
   `tests/security/test_prompt_injection.py` to parametrize over every payload,
   asserting `is_injection_attempt(payload) is True`, plus a benign block
   asserting `is False` (guards against over-blocking).
3. **Harden the defense.** Update `INJECTION_PATTERNS` so keyword/role attacks
   are matched at start-of-string as well as after a newline (e.g. anchor with
   `(?:^|\n)` and use `re.MULTILINE`). Re-run the existing
   `tests/unit/test_prompt_defense.py` to confirm no regressions.
4. **Wire CI.** Add a `test-security` job to `ci.yml` running the `security`
   marker with `LLM_PROVIDER=mock`; scope it to run on `safety/` changes.
5. **Clean up & document.** Retire `test_injection_reproduction.py` into the
   real suite, update `JOURNAL.md`, and note the newly-closed bypass.

### Inputs & outputs

- **Input:** curated attack-payload strings (from fixture files) and a set of
  benign portfolio-review strings, fed to `PromptDefense.is_injection_attempt`.
- **Output / change:** (a) a passing `security`-marked test suite that fails
  whenever a known attack stops being blocked or a benign input starts being
  blocked; (b) a hardened `INJECTION_PATTERNS` that catches first-line attacks;
  (c) a CI job producing per-commit evidence the defense holds.

### Risks & unknowns

- **Hardening may raise false positives.** Matching "System:" / "Ignore" at
  start-of-string could flag legitimate text (e.g. a résumé line starting with
  "Override"). Mitigation: keep the benign control set in the suite and tune.
- **Scope decision.** Does #71 want *only* the test suite, or also the defense
  hardening the suite exposes? If hardening is out of scope, represent known
  bypasses as `xfail(strict=True)` so they're tracked without a red build.
  Need to confirm the maintainer's intent (issue thread / Slack).
- **The defense is currently unused by app code** — `PromptDefense` is imported
  only by tests, not the request path. The suite tests the unit directly, which
  is fine for #71, but I should confirm whether wiring it into the API is in or
  out of scope.
- **CI path filtering** with `on.push.paths` interacts with required-check
  rules; a skipped job can block merges if marked required. Verify branch
  protection expectations.

### Edge cases

- Attack keywords at the very start of input (no leading newline). — primary bug
- Mixed / upper case (`SYSTEM:`, `IgNoRe`) — already `re.IGNORECASE`, keep covered.
- Whitespace variations (`   System   :`), and attacks embedded mid-paragraph.
- Unicode / homoglyph and zero-width-character variants (document if deferred).
- Benign inputs that merely mention "system", "ignore", "execute" in prose —
  must **not** be blocked (false-positive guard).
- Empty string and whitespace-only input → not an injection.
- Very long inputs (payload padded with filler) → still detected, no ReDoS.
