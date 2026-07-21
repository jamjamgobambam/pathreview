# PLAN — #146: PII scrubber fails to redact parenthesized US phone numbers

**Issue:** https://github.com/ascherj/pathreview/issues/146
**Branch:** `fix/146-pii-scrubber-paren-phone`
**Target:** the `phone_us` entry of `PII_PATTERNS` in `safety/pii_scrubber.py` (line 15)

## 1. Reproduction (verified 2026-07-20, clean checkout of `main`)

Test suite — `.venv/bin/pytest tests/unit/test_pii_scrubber.py -q`:

```
FAILED ...::TestPIIScrubber::test_us_phone_number_redaction
FAILED ...::TestPIIScrubber::test_us_phone_formats
FAILED ...::TestPIIScrubber::test_detect_phone_pii
FAILED ...::TestPIIScrubber::test_phone_at_start_of_text
FAILED ...::TestPIIScrubber::test_mixed_pii_and_text      <- separate bug, see §5
5 failed, 20 passed in 0.20s
```

The first four are exactly the tests named in the issue.

Direct reproduction of the issue's snippet (`PIIScrubber` in a REPL):

```
'(555) 123-4567'    scrub -> '(555) 123-4567'    detect -> []
'+1 555 123 4567'   scrub -> '+1 555 123 4567'   detect -> []
'555-123-4567'      scrub -> '[REDACTED]'        detect -> [('phone_us', '555-123-4567')]
'555.123.4567'      scrub -> '[REDACTED]'        detect -> [('phone_us', '555.123.4567')]
```

Both `scrub()` and `detect()` miss the parenthesized and space-separated
formats entirely; dashed/dotted formats work, so the bug is isolated to the
`phone_us` pattern's handling of spaces and the opening paren.

## 2. Root cause

Current pattern:

```python
"phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
```

Two defects:

1. **Separators exclude spaces.** Every separator class is `[-.]?` — dash or
   dot only. In `(555) 123-4567` the space after `)` can never match, so the
   match dies there; same for the spaces in `+1 555 123 4567`.
2. **Leading `\b` never matches before `(`.** `\b` requires a word char on one
   side, so at a position in front of `(` there is no boundary. The engine can
   only start matching at the first digit, meaning the `(` is never consumed:
   even space-free input like `(555)123-4567` matches only `555)123-4567`,
   which would redact to a stray `([REDACTED]`.

## 3. Proposed fix (to implement in Week 9)

```python
"phone_us": r"(?<!\w)(?:\+?1[-. ]?)?(?:\(\d{3}\)|\d{3})[-. ]?\d{3}[-. ]?\d{4}\b",
```

- `[-. ]` accepts dash, dot, or space as separators. A literal space (not
  `\s`) keeps matches from spanning newlines/tabs.
- `(?:\(\d{3}\)|\d{3})` treats the parenthesized area code as one unit: the
  `(` is consumed so the entire number is replaced, and an unbalanced paren
  can no longer half-match.
- `(?<!\w)` replaces the leading `\b` — same "not glued to a word" guarantee,
  but valid in front of `(`.
- The three capture groups are dropped: nothing reads `match.group(1..3)`;
  both `scrub()` and `detect()` use the whole match.

The exact final regex gets validated against the full suite during
implementation; this is the starting point, not a promise.

## 4. Verification plan

- The 4 issue-named tests pass; none of the currently passing 20 regress —
  in particular `123-45-6789` (SSN) must still not match `phone_us`, and
  `version 1.2.3` / URLs stay undetected (`test_detect_no_false_positives`).
- `make check` (ruff, black, mypy) and `make test-unit`.
- Manual REPL spot-check of the issue's snippet plus the §1 table.

## 5. Out of scope — and the one open question

`test_mixed_pii_and_text` fails from an **unrelated** bug: the
`street_address` pattern's `Pl` alternative under `re.IGNORECASE`, with no
trailing `\b`, matches `"5 years developing Python appl"` inside
"…worked at TechCorp for 5 years developing Python applications." — the
redaction swallows "Python" and trips `assert "Python" in scrubbed`. The
phone fix cannot make that test green.

Open question for Week 9: fix `street_address` in the same PR (keeps the
suite green but widens scope beyond #146) vs. file it as its own issue and
note the pre-existing failure in the PR description. Currently leaning:
file separately and ask the maintainers' preference on the PR.

## 6. Risks

- ~20 classmates have claimed #146; everyone submits from their own fork, so
  differentiation is repro quality, tight scope, and test coverage — not
  speed.
- Allowing spaces makes the pattern greedier (any 3-3-4 digit run like
  `555 123 4567` now redacts). For a safety layer that should prefer
  over-redaction to a PII leak, that tradeoff is acceptable and is exactly
  what `test_us_phone_formats` demands.
