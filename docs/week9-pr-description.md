# PR Description Draft

Use this title:

```text
fix(safety): redact parenthesized US phone numbers
```

Use this body:

```markdown
## Summary
This PR fixes the PII scrubber so common parenthesized US phone numbers like `(555) 123-4567` are redacted and detected the same way as existing dashed, dotted, and `+1` formats. The root cause was that the `phone_us` regex only allowed `-`, `.`, or no separator between phone-number groups, so it could not consume the space after a closing parenthesis. The updated pattern allows whitespace separators, supports balanced parenthesized area codes, and avoids matching inside longer word/digit runs.

## Issue
Closes #146

## Changes
- Updated `PIIScrubber.PII_PATTERNS["phone_us"]` in `safety/pii_scrubber.py` to match parenthesized US numbers, whitespace-separated numbers, dashed numbers, dotted numbers, and `+1` US formats.
- Preserved safeguards against partial matches inside longer tokens by using leading/trailing word-character lookarounds.
- Tightened the `street_address` suffix boundary so street abbreviations like `Pl` do not match inside unrelated words such as `applications`; this was exposed by the existing mixed-PII unit test after the phone test file became fully green.
- Expanded `tests/unit/test_pii_scrubber.py` to cover `(555)123-4567`, `+1 (555) 123-4567`, full-value phone detection, detection positions, and false-positive guards for version numbers, SSNs, and long numeric identifiers.
- Added type annotations to the touched PII scrubber test file so the repo's pre-commit Mypy hook passes on staged changes.

## Testing
- [x] Focused unit tests pass: `.venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -v` -> `25 passed`.
- [x] Linter passes for changed files: `.venv/bin/ruff check safety/pii_scrubber.py tests/unit/test_pii_scrubber.py`.
- [x] Formatter passes for changed files: `.venv/bin/black --check safety/pii_scrubber.py tests/unit/test_pii_scrubber.py`.
- [x] Pre-commit hooks pass on the committed files: Ruff, Black, and Mypy all passed during `fix(safety): redact parenthesized US phone numbers`.
- [ ] Full `make check` was run, but the repository currently reports 181 unrelated Ruff issues across pre-existing files such as `agent/`, `api/`, `rag/`, and unrelated tests before typecheck runs.
- [ ] Full `make test-unit` was run, but the repository currently has unrelated baseline failures outside this change: the PII scrubber tests pass, while other suites such as `test_bias_detector.py`, `test_review_service.py`, `test_skill_extractor.py`, and chunker tests fail independently.

Manual verification steps for reviewers:
1. Check out this branch: `git checkout fix/146-pii-parenthesized-phone`.
2. Run `python -m pytest tests/unit/test_pii_scrubber.py -v`.
3. Confirm all 25 PII scrubber tests pass.
4. In a Python shell, run:
   ```python
   from safety.pii_scrubber import PIIScrubber
   scrubber = PIIScrubber()
   print(scrubber.scrub("Call me at (555) 123-4567 or 555-123-4567"))
   print(scrubber.detect("Phone: (555) 123-4567"))
   ```
5. Confirm both phone numbers are replaced with `[REDACTED]`, and `detect()` returns a `phone_us` entry whose value is `(555) 123-4567`.

## Screenshots / Demo
Not applicable; this is a backend safety-layer regex and unit-test change.

## Notes for Reviewers
Please focus review on the US phone-number regex boundaries in `safety/pii_scrubber.py`, especially whether the pattern is broad enough for common US formats without becoming too permissive. I also included a small street-address boundary tightening because the existing mixed PII test showed the address regex could consume ordinary text ending in a word that starts with a street abbreviation (`Pl` inside `applications`).
```
