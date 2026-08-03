# Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand

`safety/pii_scrubber.py`'s `phone_us` pattern is:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

Root cause: the pattern opens with `\b`, but `\b` only fires between a word
character and a non-word character. When a phone number starts with `(`
(the parenthesized US format), the character before it in real text is a
space — both sides of that gap are non-word characters, so the boundary
never matches and the whole pattern fails to anchor. Dashed/dotted formats
work because they start with a digit, which is a word character, so the
boundary against a preceding space matches normally.

Expected: `scrub()` should replace any of the common US phone formats
(`555-123-4567`, `555.123.4567`, `(555) 123-4567`, `+1 555 123 4567`) with
`[REDACTED]`, and `detect()` should report all of them as `phone_us` PII.

Actual: parenthesized numbers pass through both `scrub()` and `detect()`
completely untouched — confirmed in
[docs/repro-146-pii-phone-numbers.md](docs/repro-146-pii-phone-numbers.md).

### Map

- `safety/pii_scrubber.py` — the only file that needs an actual code
  change; specifically the `phone_us` entry in `PII_PATTERNS` (line 15).
- `tests/unit/test_pii_scrubber.py` — no new tests needed. The four tests
  named in the issue (`test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`) already encode the
  expected behavior; the fix is done when they pass.
- Everything else in `PII_PATTERNS` (`email`, `phone_intl`, `ssn`,
  `street_address`) is untouched — `scrub()` runs each pattern in sequence
  over the same string, so I need to re-run the full file after the change,
  not just the four listed tests, to make sure nothing else regresses.

### Plan

1. Rewrite the leading boundary on `phone_us` so it tolerates `(` (or `+`)
   immediately following a non-word character, instead of requiring a
   word-character boundary right at the start. Likely a negative lookbehind
   for a word character (`(?<!\w)`) in place of the leading `\b`, kept in
   front of the optional `(?:\+?1[-.]?)?\(?` group.
2. Run `tests/unit/test_pii_scrubber.py` in full (not just the four named
   tests) to confirm the fix doesn't change behavior for `email`,
   `phone_intl`, `ssn`, or the (already separately broken, see Risks)
   `street_address` pattern.
3. Manually try a few formats not in the fixtures — `(555)123-4567` with no
   space after the parenthesis, a parenthesized number followed directly by
   a comma or period, two phone numbers of different formats in the same
   string — to check the fix generalizes past the exact test strings.
4. Re-run the reproduction steps from `docs/repro-146-pii-phone-numbers.md`
   against the fixed code and record the before/after output.
5. Write the commit using the `fix(safety): ...` convention from
   `docs/CONTRIBUTING.md` with a `Fixes #146` footer, and open the PR.

### Inputs & outputs

- Input: arbitrary text strings (resume text, generated feedback) that may
  contain zero or more US phone numbers in any of the four formats above,
  in any position in the string (start, middle, end, adjacent to other PII).
- Output of `scrub()`: the same string with every matched phone number
  substring replaced by the literal `[REDACTED]`, non-phone text left
  exactly as-is.
- Output of `detect()`: a list of dicts (`type="phone_us"`, `value`,
  `start`, `end`) with one entry per matched phone number, including
  parenthesized ones, which currently produce zero entries.

### Risks & unknowns

- A lookbehind fix could behave differently right at the very start of a
  string (no preceding character at all) versus mid-string — `test_phone_at_start_of_text`
  covers this case, so it should catch a regression, but I want to reason
  through it explicitly rather than rely on the test alone.
- Loosening the leading boundary could make the pattern start matching
  inside things that aren't phone numbers (e.g. a version string or a
  10-digit ID adjacent to punctuation) — need to sanity-check with a few
  non-phone numeric strings, not just the phone fixtures.
- `test_mixed_pii_and_text` fails today for a reason that has nothing to do
  with `phone_us` — the `street_address` pattern's suffix alternation (`Pl`
  for "Place", among others) has no trailing `\b`, so it matches the
  substring "pl" inside unrelated words like "applications" (see the repro
  doc for the full trace). This is a real, separate bug, but it's not part
  of #146's scope. I'm not fixing it as part of this PR — flagging it here
  and will ask in Slack/office hours whether it should be filed as its own
  issue or is expected to ride along since it's in the same file's test
  suite.
- Local environment: Docker and the full `make setup` stack aren't running
  on this machine yet, so everything above has only been validated at the
  unit-test level in an isolated venv (see repro doc), not through the
  actual API path that calls `PIIScrubber` before returning generated
  feedback to a user. Need to get `make run` working before Week 9 so I can
  confirm the fix holds through the real request path, not just in
  isolation.

### Edge cases

- Phone number at the very start or very end of the string (existing tests
  cover this — must keep passing).
- Parenthesized number with no space before the next digit group, e.g.
  `(555)123-4567`.
- Parenthesized number immediately followed by punctuation with no
  separating space, e.g. `"call (555) 123-4567."`.
- Multiple phone numbers of different formats in the same string (one
  dashed, one parenthesized) — both should be redacted, not just the first
  match.
- A bare 10-digit number with no separators at all (e.g. `5551234567`) —
  need to check what the current pattern already does here and make sure
  the fix doesn't change that behavior one way or the other outside of
  scope.
