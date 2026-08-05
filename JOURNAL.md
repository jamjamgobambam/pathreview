## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146
**Issue title:** PII scrubber fails to redact parenthesized US phone numbers
**Tier:** [x] Tier 1

**Problem summary:**
The phone-number regex in pii_scrubber.py uses a \b word-boundary anchor,
but ( is not a word character, so the pattern never matches when a number
opens with a parenthesized area code like (555) 123-4567. Dashed formats
like 555-123-4567 still match correctly. Because of this, scrub() leaves
parenthesized numbers in plaintext instead of redacting them, and detect()
returns an empty list even when a phone number is clearly present, which is
a real gap in a safety layer meant to catch PII. The fix is to broaden the
regex to also accept a leading parenthesis, verified by the four failing
tests already named in the issue.

**Branch name:** fix/146-pii-scrubber-parenthesized-phone
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/spicyneutrino/pathreview/commit/3977650c99490509cc8089cbb3f3d32611ad019a

**Reproduction summary:**
Ran the scrub() and detect() methods locally against a string containing
both a dashed and parenthesized phone number. Confirmed the parenthesized
format passes through unredacted and detect() returns an empty list,
matching the issue description. Also ran the four named failing tests in
test_pii_scrubber.py and confirmed they fail as expected.

**PLAN.md link:** https://github.com/spicyneutrino/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Need to confirm whether the phone_us pattern is a single regex or several
patterns, before finalizing the exact fix approach in Week 9.

## Week 9 — Fix implementation & verification

**Check-in 1**

**Progress:**
Confirmed the open question from Week 8: phone_us is a single regex, one
entry in the PII_PATTERNS dict (safety/pii_scrubber.py), used identically
by both scrub() and detect(). Root-caused the bug more precisely than the
original issue description: \b does find a valid boundary right after the
leading "(", but the pattern only accepted "-" or "." between digit groups,
not a literal space, so "555)" never bridged to " 123". Fixed with a
one-line regex change: separators now accept a literal space in addition
to "-"/"." , and the leading \b was swapped for a (?<!\w) lookbehind so the
match can start at the "(" or "+" itself (full clean redaction span, no
leftover punctuation) while keeping the exact same protection against
false positives on digits glued to a preceding letter (e.g.
"invoice5551234567" still correctly doesn't match).

Ran pytest tests/unit/test_pii_scrubber.py -v: 24 passed, 1 failed
(test_mixed_pii_and_text). That failure is pre-existing and unrelated to
this fix — it's a bug in the separate street_address pattern (a bare "Pl"
alternative for "Place" that, case-insensitively, matches the "pl" inside
ordinary words like "applications"). Confirmed via git log that the
street_address line hasn't changed since the initial commit, and via
isolated regex testing that it fails the same way with zero involvement
from phone_us. Left it untouched — out of scope for issue #146.

Ran make check: fails at the lint stage on pre-existing ruff issues spread
across unrelated files (agent/error_handling.py, agent/memory/*, etc. —
import ordering, Optional vs X | None). Isolated ruff/mypy to just
safety/pii_scrubber.py: mypy is clean, and the only ruff hits on that file
are pre-existing (unsorted imports, the already-too-long street_address
line, an unused loop variable, a too-long logger line) — none on the line
I changed.

Ran make test-unit (428 tests, whole repo): 49 failed, 379 passed. All 49
are pre-existing and unrelated (bias_detector, resume_parser,
review_service, skill_extractor, tech_detector, etc.) — within
test_pii_scrubber.py specifically, only the one expected street_address
failure shows up. The phone fix introduced zero regressions.

Manually verified extra edge cases beyond the test suite: parens with no
space ("(555)123-4567"), trailing punctuation after the number, and
multiple phone numbers in mixed formats in one string — all redact
correctly with accurate detect() spans.

**Next steps:**
Self-review the diff, then open the PR against ascherj/pathreview.

**Blockers:**
None remaining.

**Check-in 2**

**PR link:** https://github.com/ascherj/pathreview/pull/911

**Branch:** fix/146-pii-scrubber-parenthesized-phone

**What I built:**
One-line fix to the phone_us regex in safety/pii_scrubber.py: separators widened from
[-.]? to [-. ]? (3 places) so a literal space bridges "555)" to " 123", and the leading
\b anchor was swapped for (?<!\w) so the match can start at the "(" or "+" itself
(clean full-span redaction, matching detect()'s start/end contract) while keeping the
exact same protection against false positives on digits glued to a preceding letter.
Committed together with 4 small, pre-existing lint/format fixes in the same file that
pre-commit's ruff/black hooks required before any commit to this file would go through:
wrapped the overlong street_address regex literal (byte-identical content, split across
concatenated raw strings), wrapped an overlong logger.info call, renamed an unused loop
variable (pii_type -> _pii_type) in scrub(), and added the import-group blank line ruff's
I001 rule requires. None of these four change behavior.

**Tests touched:**
tests/unit/test_pii_scrubber.py — no new tests added, the existing 25 already specify
the bug (the 4 named failing tests plus the 2 already-passing edge cases from Week 8).

**Self-review confirmation:**
ruff check safety/pii_scrubber.py and mypy safety/ both pass clean with zero issues on
this file. make check's repo-wide failure (178 errors, none in this file) and make
test-unit's 49 failures are both fully pre-existing and unaffected by this change —
verified the failure lists are identical, line for line, before and after this commit,
and confirmed via git log/git diff main...HEAD that this branch's prior commits only
ever touched JOURNAL.md/PLAN.md/repro.txt, so none of it could have caused them.

**Draft PR feedback received from:** none