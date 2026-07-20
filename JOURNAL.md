# Work Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/73

**Issue title:** `pii_scrubber.py` test coverage doesn't include address formats

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer's PII scrubber (`safety/pii_scrubber.py`) is supposed to redact
personal addresses from generated feedback, but its coverage of real address
formats is incomplete and the one existing address test makes no assertions at
all, so it proves nothing. In practice, numbered street names like "5th Avenue"
or "42nd Street", house numbers with a unit letter like "221B", and PO Box
addresses are not redacted, meaning a user's address could leak through. A
successful fix adds meaningful unit tests covering these address formats and
tightens the `street_address` matching so genuine addresses are caught without
over-redacting ordinary text.

**Branch name:** test/73-pii-scrubber-address-formats

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Is this right for me? — checklist reasoning

Worked through the CodePath "Is This Issue Right for Me?" checklist:

**Part 1 — Understanding the Issue**

- [x] *I can explain the problem and expected behavior in 2–3 sentences without
  reading the issue.* In my words: the PII scrubber is meant to redact home
  addresses from generated feedback, but its address matching misses common
  real-world formats and the existing address test asserts nothing. After a fix,
  addresses like "123 5th Avenue" or "221B Baker Street" get redacted and there
  are real tests proving it.
- [x] *I've located the relevant files and confirmed they exist.*
  `safety/pii_scrubber.py` and `tests/unit/test_pii_scrubber.py` both exist.
- [x] *I can describe a concrete before-and-after.* Before: `scrub("123 5th
  Avenue")` returns the string unchanged (address leaks). After: it returns
  `"[REDACTED]"`, and ordinary text like "Room 101 upstairs" is left untouched.

**Part 2 — Tier Fit**

- [x] *The tier is a realistic match.* This is a Tier 1 issue (label `tier-1`,
  `good first issue`): a localized change in one module plus its test file, no
  cross-module or system understanding required. Appropriate as an early
  contribution rather than reaching for a Tier 3.

**Part 3 — Codebase Readiness**

- [x] *I've found and read the specific code the issue references.* Read the
  `PIIScrubber` class — the `PII_PATTERNS` dict (specifically the
  `street_address` regex), and the `scrub()` and `detect()` methods.
- [x] *I understand the surrounding code well enough to plan the fix.* The
  scrubber just applies each regex in `PII_PATTERNS` via `re.sub`/`re.finditer`;
  the fix is to broaden the `street_address` pattern (allow digits in
  street-name words, a unit letter on the house number) and add a `po_box`
  pattern — no callers need to change.
- [x] *I've read the test file and at least one test end-to-end.* Read
  `tests/unit/test_pii_scrubber.py`, including `test_address_variations` (which
  runs `scrub()` but makes no assertions) and `test_detect_returns_list_of_pii`.

**Part 4 — Scope and Time**

- [x] *Not already claimed (comments + ledger).* No comments claiming issue #73
  on GitHub as of selection. NOTE: I could not view the cohort ledger myself —
  needs a manual confirm that it isn't taken there.
- [x] *Scope realistic for Weeks 8–9.* This is a small Tier 1 change (~3–6h of
  the regex-and-tests kind) that fits comfortably within the two-week window.
- [x] *No blockers or dependencies.* The issue body references no "blocked by"
  issue and the code is self-contained.

**Scope boundary:** I'll keep this change to address-format coverage in the PII
scrubber. A related-but-separate problem I noticed — the phone-number regex
failing on formats like `(555) 123-4567` — is out of scope and belongs in its
own issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/raeesahiram/pathreview/commit/024b02339727694f5ae7f9ba7822bd50fd620bf4

**Reproduction summary:**
I ran `scrub()` / `detect()` against a set of real address formats and observed
that `123 5th Avenue`, `221B Baker Street`, and `PO Box 1234` pass through
unredacted (and `detect()` returns `[]`), while the existing address tests still
report as passing because `test_address_variations` has no assertions.

**PLAN.md link:** https://github.com/raeesahiram/pathreview/blob/main/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Whether ZIP-code redaction is expected as part of "address formats." I've scoped
it out of the fix for now (a bare 5-digit pattern would over-redact any number)
and will confirm before finalizing in Week 9.

### Reproduction detail

Confirmed the issue is real on an untouched `main` (working tree clean, no code
changes made during reproduction).

**Where it lives:**
- `safety/pii_scrubber.py:18` — the `street_address` regex in `PII_PATTERNS`.
- `tests/unit/test_pii_scrubber.py:193` — `test_address_variations`, which has
  no assertions.

**How to reproduce (functional leak):**

```python
from safety.pii_scrubber import PIIScrubber
s = PIIScrubber()
print(s.scrub("123 5th Avenue"))     # -> "123 5th Avenue"   (should be [REDACTED])
print(s.scrub("221B Baker Street"))  # -> "221B Baker Street" (should be [REDACTED])
print(s.scrub("PO Box 1234"))        # -> "PO Box 1234"       (should be [REDACTED])
print(s.detect("221B Baker Street")) # -> []                  (nothing flagged)
```

Observed vs. expected:

| Input | `scrub()` today | Expected |
|---|---|---|
| `123 Main St` | `[REDACTED]` | `[REDACTED]` (already works) |
| `123 5th Avenue` | `123 5th Avenue` | `[REDACTED]` |
| `123 42nd Street` | `123 42nd Street` | `[REDACTED]` |
| `221B Baker Street` | `221B Baker Street` | `[REDACTED]` |
| `PO Box 1234` | `PO Box 1234` | `[REDACTED]` |

**Root cause:** the name portion `[A-Za-z\s]+` rejects digits, so numbered
street names (`5th`, `42nd`) never match; `\d+` alone won't accept a lettered
house number (`221B`); and there is no PO-box pattern at all.

**How to reproduce (test-coverage gap):**

```
$ .venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -q -k "address"
3 passed
```

The address tests pass even though the leaks above exist, because
`test_address_variations` calls `scrub()` in a loop but never asserts anything —
so there is effectively no real address-format coverage.

Reproduction is deterministic (pure regex; no network or LLM involved).
