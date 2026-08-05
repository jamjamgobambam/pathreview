# PLAN — #146: PII scrubber fails to redact parenthesized US phone numbers

**Branch:** `fix/146-pii-scrubber-paren-phone`

## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers — ascherj/pathreview#146](https://github.com/ascherj/pathreview/issues/146)

### Understand

**Expected:** every common written US phone format — `555-123-4567`,
`555.123.4567`, `(555) 123-4567`, `+1 555 123 4567` — is replaced by
`[REDACTED]` by `scrub()` and reported by `detect()`, so resume text never
carries a phone number into LLM prompts or stored review output.

**Actual (reproduced 2026-07-20 on a clean checkout):**

```
'(555) 123-4567'    scrub -> '(555) 123-4567'    detect -> []
'+1 555 123 4567'   scrub -> '+1 555 123 4567'   detect -> []
'555-123-4567'      scrub -> '[REDACTED]'        detect -> [('phone_us', '555-123-4567')]
'555.123.4567'      scrub -> '[REDACTED]'        detect -> [('phone_us', '555.123.4567')]
```

`pytest tests/unit/test_pii_scrubber.py -q` → **5 failed / 20 passed**; four
of the failures are exactly the tests named in the issue
(`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`). The fifth
(`test_mixed_pii_and_text`) fails from an unrelated `street_address` bug —
see *Risks & unknowns*.

**Root cause** — the `phone_us` pattern:

```python
"phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
```

1. Every separator class is `[-.]?` (dash/dot only), so the space after `)`
   in `(555) 123-4567` — and the spaces in `+1 555 123 4567` — kill the
   match.
2. The leading `\b` requires a word character on one side, so it can never
   match in front of `(`. The engine can only start at the first digit,
   meaning even space-free `(555)123-4567` matches as `555)123-4567`, and
   redaction would leave a stray `(`.

### Map

| File | Role in the fix |
|---|---|
| `safety/pii_scrubber.py` | The only production change: the `phone_us` entry of `PII_PATTERNS` (line 15). `scrub()` / `detect()` bodies stay untouched. |
| `tests/unit/test_pii_scrubber.py` | Four existing tests already encode the expected behavior; add one regression test for full-paren consumption (`(555)123-4567` → no stray `(`). |

Verified blast radius: `grep -rn "PIIScrubber\|pii_scrubber"` finds **no
production call sites yet** — only the module itself and its unit tests (the
safety middleware chain that will consume it is separate work, cf. issue
#75). The fix is a regex-constant swap with fully local effects.

### Plan

1. Replace `phone_us` with a pattern that accepts space separators and
   consumes the parenthesized area code as a unit. Starting point (final
   form driven by the tests):
   `r"(?<!\w)(?:\+?1[-. ]?)?(?:\(\d{3}\)|\d{3})[-. ]?\d{3}[-. ]?\d{4}\b"`
   — `[-. ]` adds the space separator, `(?:\(\d{3}\)|\d{3})` makes the `(`
   part of the match, `(?<!\w)` replaces the leading `\b` (same "not glued
   to a word" guarantee, but valid before `(`), and the unused capture
   groups are dropped.
2. Iterate against `pytest tests/unit/test_pii_scrubber.py` until the four
   issue-named tests pass with zero regressions among the 20 currently
   green.
3. Add a regression test: `(555)123-4567` scrubs to `[REDACTED]` with no
   leftover `(`, and `detect()` spans cover the full match including `(`.
4. Run `make check` (ruff/black/mypy) and `make test-unit`; REPL spot-check
   the issue's own reproduction snippet.
5. Open the PR from the fork using the PR template; link the reproduction
   commit and note the pre-existing `test_mixed_pii_and_text` failure (plus
   the separately-filed street_address issue, pending the scope decision
   below).

### Inputs & outputs

- **Input:** arbitrary user text passed to `PIIScrubber.scrub(text)` /
  `.detect(text)` — resume content and generated review text.
- **Output:** `scrub()` returns the text with the *entire* phone string
  (opening paren included) replaced by `[REDACTED]`; `detect()` returns
  `{"type": "phone_us", "value", "start", "end"}` entries whose spans cover
  the full number. No signature, return-shape, or config changes —
  behavior-only.

### Risks & unknowns

- **Over-matching by design:** allowing spaces means any 3-3-4 digit run
  (`555 123 4567`) now redacts. For a safety layer, over-redaction beats a
  PII leak — and `test_us_phone_formats` explicitly demands this format.
  `test_detect_no_false_positives` guards the opposite direction.
- **Pattern interplay:** `phone_intl` and `ssn` must keep matching exactly
  what they match today (`+44 20 7946 0958` stays intl; `123-45-6789` is
  3-2-4 and must never match `phone_us`). Full-suite runs cover this.
- **Known-red neighbor test:** `test_mixed_pii_and_text` fails because the
  `street_address` pattern's `Pl` alternative under `IGNORECASE` (and no
  trailing `\b`) matches "5 years developing Python appl", swallowing
  "Python". The phone fix cannot green it. **Open question:** fix
  `street_address` in the same PR vs. file it as its own issue and note the
  pre-existing failure in the PR description — leaning toward a separate
  issue, will ask the maintainers' preference on the PR.
- **Cohort parallelism:** ~20 classmates claimed #146; differentiation is
  scope discipline and test quality, not speed.

### Edge cases

- Phone at the very start of the text: `(555) 123-4567 is my number.`
- No space after the paren: `(555)123-4567` — the `(` must be consumed, no
  stray paren in the output.
- Unbalanced paren: `(555 123 4567` — the bare-digit branch still redacts
  `555 123 4567`; the stray `(` remains but no digits leak.
- Country-code variants: `+1 555 123 4567`, `1-555-123-4567`, and a bare
  11-digit run `15551234567`.
- Non-phones that must stay untouched: SSN `123-45-6789`, version strings
  like `1.2.3`, URLs (`test_detect_no_false_positives`).
- Idempotency: scrubbing already-scrubbed text is a no-op (`[REDACTED]`
  contains no digits) — `test_scrub_idempotent`.
- Multi-line text: the literal-space separator (deliberately not `\s`)
  stops matches from spanning newlines — `555\n123 4567` is two fragments,
  not one phone.
- Empty / whitespace-only input (`test_empty_text`, `test_whitespace_only`).
