# Issue #64 Solution Plan

## Solution plan

**Issue:** [Prompt injection defense doesn't sanitize newline characters in user-supplied resume text (#64)](https://github.com/ascherj/pathreview/issues/64)

### Understand

`PromptDefense.is_injection_attempt()` in `safety/prompt_defense.py` detects prompt-boundary separators such as `\n---\n` and newline-prefixed role labels such as `\nSystem:`. However, `PromptDefense.sanitize()` only removes template delimiters and angle brackets, so it returns those newline injection sequences unchanged. The expected behavior is for sanitization to neutralize prompt-boundary and role-switch sequences without flattening or otherwise damaging ordinary multiline resume content. The actual behavior can be reproduced by sanitizing a malicious multiline string and observing that the dangerous substring remains and the sanitized result is still recognized as an injection attempt.

### Map

Files involved in the focused fix:

- `safety/prompt_defense.py`
  - `PromptDefense.sanitize()` is the defective function.
  - `PromptDefense.INJECTION_PATTERNS` defines related detection behavior that should remain consistent with sanitization.
- `tests/unit/test_prompt_defense.py`
  - Add the failing reproduction and regression coverage for malicious and benign multiline inputs.
- `JOURNAL.md`
  - Record the Week 8 reproduction commit, reproduction result, plan link, and any remaining uncertainty.
- `PLAN.md`
  - Maintain this plan as the investigation evolves.

A repository-wide search found no production caller of `PromptDefense` outside its module and unit tests. Adding prompt defense to the resume ingestion or review pipeline is therefore outside the issue's stated file scope unless maintainer feedback confirms that integration is required.

### Plan

1. Add a parameterized failing test in `tests/unit/test_prompt_defense.py` proving that `sanitize()` leaves both a separator boundary (`\n---\n`) and a role-switch boundary (`\nSystem:`) in its output; commit this test separately as the Week 8 reproduction.
2. Define the intended neutralization behavior in tests, including preservation of normal line breaks and meaningful resume text, then cover case and whitespace variants that the detector treats as malicious.
3. Update `PromptDefense.sanitize()` in `safety/prompt_defense.py` to neutralize only injection-shaped newline sequences while retaining ordinary multiline formatting and the existing template/angle-bracket behavior.
4. Add regression tests for LF and CRLF input, supported role labels, separator lengths, benign multiline resumes, empty input, and repeated sanitization.
5. Run the focused prompt-defense tests followed by formatting, linting, type checking, and the full unit suite; update `JOURNAL.md` with links and any plan changes before submitting the branch URL.

### Inputs & outputs

The fix takes a Python `str` containing untrusted, potentially multiline resume text. Inputs may contain ordinary paragraphs as well as prompt-like separator lines, role labels, mixed capitalization, indentation, or Windows/Unix newline sequences. `sanitize()` should return a string in which supported prompt-boundary and role-switch sequences can no longer act as new prompt instructions, while legitimate text, paragraph boundaries, and the method's existing delimiter sanitization are preserved. Running `sanitize()` more than once should produce the same result as running it once.

### Risks & unknowns

- `safety/prompt_defense.py` currently separates detection patterns from sanitization logic. Duplicating regexes could allow the two behaviors to drift, so tests must verify that sanitized malicious samples are no longer recognized by the corresponding newline-injection rules.
- A separator such as `---` can be legitimate Markdown or resume formatting. Replacing every newline would be destructive, while removing every horizontal rule may cause false positives; the implementation should target only the prompt-boundary shape and preserve surrounding content.
- The existing role-switch detector requires a colon immediately after `System`, `Human`, or `Assistant`, although one current test uses whitespace before the colon. The issue does not state whether sanitization must support that wider variant, so this should be resolved through a test-backed interpretation or maintainer feedback rather than an unrelated detector rewrite.
- `PromptDefense` has no production call site found by repository search. This plan addresses the issue's named `sanitize()` defect; wiring it into `api/routes/profiles.py`, `core/services/review_service.py`, or another ingestion path would be a separate security design decision unless maintainers confirm otherwise.
- The local environment must have development dependencies installed before the reproduction and regression suites can provide trustworthy results.

### Edge cases

- Unix `\n`, Windows `\r\n`, and mixed newline input.
- Separator lines with three or more hyphens, surrounding spaces, indentation, and trailing whitespace.
- `System:`, `Human:`, and `Assistant:` with mixed capitalization and indentation.
- A role word used normally inside a sentence, such as “Designed a system: monitoring dashboard.”
- Legitimate multiline resumes containing paragraphs, headings, bullet lists, and Markdown separators.
- Multiple injection patterns in one string and malicious patterns at different line positions.
- Empty strings, whitespace-only input, and text already sanitized once.
- Existing template delimiters and angle brackets combined with newline injection patterns.
