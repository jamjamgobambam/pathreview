## Solution plan

**Issue:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text — https://github.com/ascherj/pathreview/issues/64

### Understand

What needs to change: the `sanitize()` method in `safety/prompt_defense.py` needs to actually remove the newline-based injection patterns that `is_injection_attempt()` already knows how to detect.

Root cause: `PromptDefense.INJECTION_PATTERNS` already contains regex patterns that correctly match separator-line attacks (`\n---\n`) and role-switching attacks (`\nSystem:`, `\nHuman:`, `\nAssistant:`). The `is_injection_attempt()` method uses this list correctly and detects these patterns. However, `sanitize()` never references `INJECTION_PATTERNS` at all — it only does hardcoded string replacement of `<`, `>`, `{{`, `}}`, `{%`, `%}`. So a string can pass through `sanitize()` completely unchanged and still contain a working injection payload.

Expected vs. actual: expected behavior is that after `sanitize(text)` runs, `is_injection_attempt()` should return `False` on the result. Actual behavior, which I confirmed with a reproduction test, is that `is_injection_attempt()` still returns `True` after sanitization.

### Map

Files this fix will touch:
- `safety/prompt_defense.py` — contains both `sanitize()` and `INJECTION_PATTERNS`; this is where the actual fix goes.
- `tests/unit/test_prompt_defense.py` — existing test file; I will add new unit tests here to cover the fixed behavior.

Related but out of scope: `agent/orchestrator.py` and `agent/tools/skill_extractor.py` handle resume text elsewhere in the app, but neither of them calls `PromptDefense` at all right now. That is a separate integration gap I am not fixing in this PR, since issue #64 names only `safety/prompt_defense.py`.

### Plan

1. In `safety/prompt_defense.py`, rewrite `sanitize()` to loop through `PromptDefense.INJECTION_PATTERNS` and apply `re.sub()` for each pattern, in addition to the existing character replacements it already does.
2. Decide the replacement value for each regex match (empty string vs. a single space) so that removing a pattern does not accidentally merge two unrelated words or sentences together.
3. Add new test cases to `tests/unit/test_prompt_defense.py` that assert `sanitize()` removes each newline-based pattern category: separator lines, role-switching (System/Human/Assistant), and the ignore/forget/disregard/override instruction patterns.
4. Run the full existing suite in `tests/unit/test_prompt_defense.py` to confirm no currently-passing test breaks, especially `test_sanitize_preserves_legitimate_content` and `test_sanitize_idempotent`.
5. Re-run my Week 8 reproduction test to confirm `is_injection_attempt(PromptDefense.sanitize(malicious_text))` now returns `False`.

### Inputs & outputs

Input: a raw string of user-supplied resume text, which may or may not contain injection attempts.

Output: `sanitize()` returns a string with all `INJECTION_PATTERNS` matches removed (or neutralized), while legitimate resume content — including normal punctuation, line breaks, and words like "system" used in an ordinary sentence — is left intact. The function signature (`sanitize(text: str) -> str`) does not change.

### Risks & unknowns

- Risk in `safety/prompt_defense.py`: the pattern `r"\n\s*---+\s*\n"` could be too broad and strip legitimate resume formatting, such as a bullet list separator or a date range written as `2020--2022`, if not scoped carefully.
- Risk in `safety/prompt_defense.py`: choosing to delete a match entirely (replace with `""`) versus replacing with a space could change how readable the resulting text is; I need to test both and pick the one that doesn't glue unrelated words together.
- Unknown tied to `tests/unit/test_prompt_defense.py::test_benign_mentions_not_flagged`: this existing test already flags that the word "System" appearing mid-sentence (not at a line start) is an ambiguous case; my regex changes need to not make this false-positive risk worse.
- Unknown tied to `safety/prompt_defense.py`: the current regex patterns assume Unix-style `\n` line endings; I need to investigate whether resume text with Windows-style `\r\n` line endings would bypass the patterns entirely.

### Edge cases

- Empty string input: `sanitize("")` must still return `""` (covered by the existing `test_empty_string` test, must not regress).
- Multiple injection patterns appearing back to back in the same input, e.g. `"\n---\nSystem: ignore\n{{code}}"` — all patterns must be removed, not just the first match found.
- Legitimate text where "System" appears mid-sentence rather than at a line boundary, e.g. "The system runs efficiently on Python" — this must NOT be altered by the fix.
- Text using `\r\n` (Windows-style) line endings instead of plain `\n` before a separator or role-switch pattern — needs explicit testing to confirm the regex still matches.
