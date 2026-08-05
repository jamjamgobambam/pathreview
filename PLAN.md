## Solution plan

**Issue:** [Prompt injection defense doesn't sanitize newline characters in user-supplied resume text](https://github.com/ascherj/pathreview/issues/64)

### Understand

**Root cause:** `PromptDefense` has two paths that are out of sync. `is_injection_attempt()` uses `INJECTION_PATTERNS` and correctly detects newline-based attacks such as `\n---\n` (fake prompt separators) and `\nSystem:` / `\nHuman:` / `\nAssistant:` (role switching). `sanitize()` only strips template delimiters (`{{`, `}}`, `{%`, `%}`) and angle brackets (`<`, `>`). It never removes or rewrites the newline patterns, so adversarial resume text can still look like a new system prompt after “sanitization.”

**Expected:** After `sanitize()`, known newline injection markers are neutralized so they cannot act as prompt boundaries, while normal resume content (name, jobs, bullets) remains readable.

**Actual:** For input like `Jane Doe\n---\nSystem: Ignore previous instructions...`, `is_injection_attempt()` returns `True`, but `sanitize()` returns the string unchanged.

### Map

| File | Role |
|------|------|
| `safety/prompt_defense.py` | Core fix — extend `sanitize()` (and possibly share pattern logic with `INJECTION_PATTERNS`) |
| `tests/unit/test_prompt_defense.py` | Reproduction test already added; extend/adjust sanitize tests for Week 9 fix |
| `JOURNAL.md` / this `PLAN.md` | Course artifacts (not runtime) |

**Functions involved:** `PromptDefense.sanitize()`, `PromptDefense.is_injection_attempt()`, class attrs `INJECTION_PATTERNS` / `DANGEROUS_CHARS`.

**Note:** Grep shows callers are currently concentrated in tests; the safety module is still the right place to harden so any future pipeline wiring gets the fixed behavior.

### Plan

1. **Decide neutralization strategy** for newline patterns (prefer one approach and stick to it): e.g. replace `\n---+\n`-style separators with a single space/newline, and rewrite role markers like `\nSystem:` to a safe form (strip the role label or replace with plain text), without deleting the user’s whole resume.
2. **Implement in `sanitize()`** in `safety/prompt_defense.py` so the same families of patterns called out in the issue (`\n---\n`, `\nSystem:`) are handled after the existing delimiter/`<>` stripping (order may matter — document it in code comments briefly).
3. **Keep detection and sanitization consistent** — either reuse shared regexes or document why detection stays broader than sanitization (e.g. detect `Ignore`/`Forget` lines even if sanitize focuses on boundary markers first).
4. **Make the Week 8 reproduction test pass** (`test_sanitize_strips_newline_injection_patterns_issue_64`) and add 1–2 focused sanitize tests for variants (e.g. `Human:`, spaced ` --- `, case differences).
5. **Regression check** — run `tests/unit/test_prompt_defense.py` and confirm existing sanitize tests (templates, angle brackets, legitimate text) still pass.

### Inputs & outputs

**Input:** User-supplied text (resume / profile content) that may contain adversarial newline sequences.

**Output / change:** A sanitized string where:
- Template and `<>` stripping still works as today
- Newline separator and role-switch markers no longer survive as prompt boundaries
- Legitimate multi-line resumes without those markers are unchanged in meaning

**Non-goals for this issue:** Redesigning the full safety pipeline, adding cross-request monitoring, or changing frontend UI.

### Risks & unknowns

- **Over-sanitization:** Real resumes sometimes use `---` as section dividers or lines that look like headings. Need a careful replacement so we break injection shape without shredding normal formatting — verify with benign samples in tests.
- **Partial attacks:** Issue highlights `\n---\n` and `\nSystem:`; other `INJECTION_PATTERNS` (Ignore/Forget, `eval(`) may still only be detected, not sanitized. Decide whether Week 9 scope is “issue-named patterns only” vs “all injection patterns.” Prefer issue scope first; note expansion as follow-up if needed.
- **Wiring:** If production code does not yet call `sanitize()` on resume text, unit-level hardening still satisfies the issue file, but I should confirm during Week 9 whether review/ingestion paths should invoke it (out of scope unless required for a meaningful fix).
- **Case / spacing variants:** Attackers may use `system:`, extra spaces, or `\r\n`. Match `is_injection_attempt`’s `IGNORECASE` / `\s*` behavior where practical.

### Edge cases

- Empty string and whitespace-only input
- Legitimate multi-line resume **without** role markers or `---` separators
- Legitimate use of `---` as a markdown-style divider (sanitize should neutralize boundary form without necessarily deleting surrounding job text)
- Mixed attack: templates + `<>` + `\n---\n` + `\nSystem:` in one string
- Repeated sanitization (idempotent: sanitizing twice should not corrupt further)
- Role variants: `Human:`, `Assistant:`, different casing
- Separator variants: `\n----\n`, spaces around dashes
