# Solution plan

**Issue:** [#64 Prompt injection defense doesn't sanitize newline characters in user-supplied resume text](https://github.com/ascherj/pathreview/issues/64)

### Understand

**Root cause.** `safety/prompt_defense.py` exposes two static methods that are meant to
work together.

- `sanitize(text)` cleans untrusted text so it is safe to embed in a prompt. It only
  removes template/markup delimiters (`{{ }}`, `{% %}`, `<`, `>`). It never touches
  newlines.
- `is_injection_attempt(text)` *detects* injection, and its `INJECTION_PATTERNS`
  already include the newline separator (`\n\s*---+\s*\n`) and role-switch
  (`\n\s*(?:System|Human|Assistant):`) patterns.

So the module already knows `\n---\n` and `\nSystem:` are dangerous, but `sanitize()`
does nothing about them. A resume containing a line break followed by `---` or `System:`
survives sanitization and can terminate the system prompt or inject a new instruction turn.

There is also a secondary defect in detection. The role-switch pattern requires the colon
immediately after the role word, so `System  :` (spaces before the colon) is **not**
detected, which is why `tests/unit/test_prompt_defense.py::test_whitespace_variations_detected`
currently fails.

**Expected versus actual.**

| Input | Expected | Actual (today) |
|---|---|---|
| `sanitize("...\nSystem: ignore...")` | role-switch marker removed/neutralized | returned unchanged |
| `sanitize("...\n---\n...")` | separator line removed/neutralized | returned unchanged |
| `is_injection_attempt("...\n   System  :  ignore")` | `True` | `False` |

### Map

Files I expect to touch.

- **`safety/prompt_defense.py`** is the primary fix. Update `sanitize()` to neutralize the
  newline separator and role-switch patterns, and tighten the role-switch regex in
  `INJECTION_PATTERNS` to allow whitespace before the colon.
- **`tests/unit/test_prompt_defense_newline_repro.py`** holds the reproduction tests I added
  in Week 8. They should flip from failing to passing (no edits expected, they define the
  target behavior).
- **`tests/unit/test_prompt_defense.py`** holds the existing `test_whitespace_variations_detected`,
  which should pass once the detection regex is fixed. I may add a few `sanitize()`
  assertions here so the fix is covered in the canonical test file too.

Out of scope but noted. `PromptDefense` is not currently imported by any non-test module,
so the whole `safety/` layer is standalone utilities. Wiring it into the ingestion or
prompt pipeline is a separate concern and outside this issue.

### Plan

1. **Define single-source patterns.** Factor the separator and role-switch regexes into
   named module-level constants so `sanitize()` and `is_injection_attempt()` use the *same*
   definitions. This avoids the two methods drifting apart again, which is the root cause
   of this bug.
2. **Fix `sanitize()`.** After the existing delimiter stripping, run regex substitutions
   that neutralize the newline attacks. Collapse a matched separator line to a single
   space and de-anchor a role-switch marker (for example, replace the leading newline so
   `System:` can no longer read as the start of a new turn), while preserving ordinary
   text and ordinary paragraph newlines.
3. **Fix the detection regex.** Change `\n\s*(?:System|Human|Assistant):` to allow optional
   whitespace before the colon (`...\s*:`), so `System  :` is caught. This makes
   `test_whitespace_variations_detected` pass.
4. **Verify with tests.** Run the Week 8 reproduction file and the existing
   `test_prompt_defense.py`, and confirm all pass. Add a few direct `sanitize()`
   assertions and confirm `sanitize()` is idempotent and doesn't corrupt clean resumes.
5. **Confirm no regressions.** Re-run the full unit suite and confirm the prompt-defense
   module goes to 0 failures without breaking anything else.

### Inputs and outputs

- **Input.** An arbitrary user-supplied `str` (resume or portfolio text), including one that
  contains newline-based injection payloads.
- **Output of `sanitize()`.** A `str` with template delimiters, angle brackets, **and**
  newline separator or role-switch markers neutralized, while legitimate content and normal
  paragraph breaks are preserved. The post-condition is that `is_injection_attempt(sanitize(x))`
  is `False` for the payloads in the reproduction tests.
- **Output of `is_injection_attempt()`.** Unchanged contract (`bool`), but now also returns
  `True` for whitespace-before-colon role switches.

### Risks and unknowns

- **Over-stripping legitimate resumes.** Real resumes use `---` as a visual divider and
  lines like `Summary:` or `Skills:`. If neutralization is too aggressive it will mangle
  normal content. To mitigate, the role-switch pattern is limited to the specific tokens
  `System|Human|Assistant`, and I'll add a "clean resume is preserved" assertion. The risk
  lives in `sanitize()` in `safety/prompt_defense.py`.
- **Behavior choice, strip versus escape.** Removing the marker versus breaking it (for
  example inserting a space) produce different output text. The open question is whether any
  downstream consumer cares about exact output. I checked with
  `grep -rn "PromptDefense\|\.sanitize(" --include=*.py`, which currently returns no non-test
  callers, so I have latitude, but I'll keep output minimal.
- **Regex drift and ReDoS.** Loosening `\s*` around patterns risks catastrophic backtracking on
  pathological input. To mitigate, I'll keep quantifiers simple and bounded and test with a long
  adversarial string.
- **Test expectations elsewhere.** Changing detection could affect other assertions in
  `tests/unit/test_prompt_defense.py` (for example `test_benign_mentions_not_flagged`). I'll run the
  whole file, not just my new tests.

### Edge cases

- Clean resume with normal paragraph newlines (`"...Python.\nProjects...\n"`) stays **not**
  altered and **not** flagged (guard against false positives).
- Legitimate section header `Summary:` at line start (no `System/Human/Assistant`) stays preserved.
- `System  :` and `system:` (extra spaces, mixed case) get detected and neutralized.
- Long separator `--------` and minimal `---` both get neutralized.
- Multiple payloads in one input (`\nSystem: ...\n---\n{{x}}`) all get neutralized in one pass.
- Empty string or whitespace-only string returns unchanged and not flagged (already covered).
- `sanitize(sanitize(x)) == sanitize(x)` (idempotent) must still hold after the fix.
