## Solution plan

**Issue:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand

The `phone_us` pattern in `safety/pii_scrubber.py` is:

```python
r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
```

It already has optional `\(?` / `\)?` groups around the area code, so it looks like parentheses are supported. The actual bug is narrower: the separator allowed immediately after the closing `)` is `[-.]?`, which does not include a literal space. The conventional parenthesized US format is written `(555) 123-4567` — space, not dash or dot, after the `)`. Because of that, the regex engine can match up through the closing paren but then fails to bridge the space before the next 3-digit group, so the whole match attempt fails and the number is skipped entirely.

Expected behavior: `scrub()` should replace `(555) 123-4567` with `[REDACTED]`, and `detect()` should return a `phone_us` entry for it, exactly as it already does for `555-123-4567`.

Actual behavior (confirmed via `scripts/repro_issue_146.py`): `scrub()` leaves `(555) 123-4567` untouched while still correctly redacting `555-123-4567` in the same string, and `detect()` returns `[]` when a parenthesized number is the only PII present in the text.

### Map

Files expected to be touched:

- `safety/pii_scrubber.py` — update the `phone_us` regex pattern (the only line that needs to change is the pattern string in `PII_PATTERNS`).
- `tests/unit/test_pii_scrubber.py` — the existing tests `test_us_phone_number_redaction`, `test_us_phone_formats`, and any new `detect()`-focused test I add for the parenthesized case. These currently fail and should pass once the regex is fixed. I may add one new test explicitly asserting `detect()` returns a `phone_us` match for `(555) 123-4567` alone, since that's the sharpest reproduction of the bug.
- `scripts/repro_issue_146.py` — already added this week as reproduction evidence; no further changes expected, but I'll re-run it after the fix to confirm the "before" output in its docstring flips to the redacted/detected form.
- `JOURNAL.md` — Week 9 entry documenting the fix.

No other modules import or depend on `PIIScrubber` yet (confirmed via repo-wide search), so the blast radius is contained to this one file and its tests.

### Plan

1. ✅ Write/confirm a failing test that isolates the exact gap: `detect()` on text containing only `(555) 123-4567` should return one `phone_us` match (currently returns `[]`). Added `test_detect_parenthesized_phone_only`.
2. ✅ Update the `phone_us` regex in `safety/pii_scrubber.py`: widened the separator after the optional closing `)` (and elsewhere) to `[-.\s]?`, and replaced the leading `\b` with `(?<!\w)` so a leading `(`/`+` is included in the redacted match rather than left behind.
3. ✅ Verified the full `phone_us`-related test list (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`) plus the rest of `test_pii_scrubber.py` against the updated pattern — no regressions in email/SSN/address/no-PII/international-phone cases. Added 3 new tests: `test_detect_parenthesized_phone_only`, `test_scrub_parenthesized_and_dashed_phone_together`, `test_phone_us_space_separated_tradeoff`.
4. ✅ Updated `scripts/repro_issue_146.py`'s docstring with the confirmed before/after output and a note on the accepted trade-off.
5. ⬜ Run `make check && make test-unit` locally (needs the project venv, not available in the sandbox I was working in) and confirm both pass before opening the PR. Write the commit message following Conventional Commits with a `safety` scope.

### Inputs & outputs

**Input:** free-form text strings passed to `PIIScrubber.scrub(text)` and `PIIScrubber.detect(text)` that may contain US phone numbers in dashed (`555-123-4567`), dotted (`555.123.4567`), plain (`+1 555 123 4567`), or parenthesized (`(555) 123-4567`) form, possibly mixed with other PII types (email, SSN, address) in the same string.

**Output:** `scrub()` returns the text with every recognized phone number (including the parenthesized form) replaced by `[REDACTED]`. `detect()` returns a list of dicts (`type`, `value`, `start`, `end`) that includes an entry for the parenthesized form with correct offsets into the original string, matching the shape it already returns for the other formats.

### Risks & unknowns

- **Over-broad matching risk (confirmed, accepted):** I verified this directly — widening the separator to `[-.\s]?` does cause `phone_us` to match bare 3-3-4 digit sequences separated only by spaces even when they aren't phone numbers, e.g. `"order 123 456 7890 units"` now matches. I'm accepting this trade-off rather than narrowing the fix, because (a) it's needed to make the space-separated `+1 555 123 4567` format work too — see the `phone_intl` finding below — and (b) over-redaction is the safer failure mode for a PII scrubber than under-redaction. Documented in a code comment above the pattern and covered by `test_phone_us_space_separated_tradeoff` in `tests/unit/test_pii_scrubber.py`, and in `scripts/repro_issue_146.py`'s docstring.
- **Interaction with `phone_intl` (confirmed, resolved):** I found that `+1 555 123 4567` was *already* failing to match under the original `phone_us` pattern (space after "1" isn't in `[-.]?`), and it also doesn't match `phone_intl` (`\+[0-9]{1,3}[-.]?[0-9]{1,14}`, which also requires `-`/`.`/nothing, not a space, right after the digits). So `test_us_phone_formats` was actually failing for two separate reasons, not just the parenthesized case — the issue just doesn't call that out explicitly. My widened `phone_us` pattern also fixes the `+1 555 123 4567` sub-case directly, so `phone_intl` never even needs to see that string. No `phone_intl` regressions observed (`+44 20 7946 0958` still redacts correctly).
- **Regex readability/maintainability:** addressed by adding an explanatory comment block directly above the `phone_us` pattern in `safety/pii_scrubber.py` explaining the `(?<!\w)` lookbehind, the widened separator class, and the accepted trade-off, so the next contributor doesn't have to reverse-engineer it.
- **Resolved — leading `(` / `+` left unredacted:** initial attempts at the fix (just widening `[-.]?` to `[-.\s]?`) left a stray `(` or `+` character behind after redaction (e.g. `"Call me at ([REDACTED]"`), because the original leading `\b` assertion can't fire immediately before a non-word character like `(` when it's preceded by whitespace. Replaced the leading `\b` with `(?<!\w)`, which allows the match to include the leading `(`/`+` while still refusing to match mid-word (verified `"foo(555) 123-4567"` does not swallow part of `"foo"`).

### Edge cases

- `(555) 123-4567` — the reported bug case; must be redacted/detected.
- `(555)123-4567` — parens with no space after `)`; already passes today per the existing pattern, must not regress.
- `(555) 123.4567` — mixed space-then-dot separator; should be handled if the fix generalizes the separator class rather than special-casing exactly one space.
- Parenthesized number at the very start of a string (per `test_phone_at_start_of_text`) — confirms the `\b` boundary logic still works when there's no leading whitespace before the `(`.
- Parenthesized number immediately followed by punctuation, e.g. `Call (555) 123-4567.` — trailing period shouldn't be swallowed into or block the match.
- A string with both a parenthesized number and an unrelated space-separated pair of numbers that isn't a phone number (e.g. "room 123 4567 sq ft") — should NOT be falsely redacted; this is the main regression risk from widening the separator.
- Text with no phone number at all (`test_text_with_no_pii`) — must remain completely unchanged.
