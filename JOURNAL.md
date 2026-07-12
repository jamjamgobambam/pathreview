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

### Is this right for me? — selection notes

I worked through the selection checklist before claiming this issue:

- **Scope is small and self-contained.** The change is limited to one module
  (`safety/pii_scrubber.py`) plus its unit test file. No API, database, or
  cross-cutting changes are required.
- **Tier fit.** It carries the `tier-1` and `good first issue` labels, which
  matches where I should be starting.
- **I understand the problem and can define "done."** The scrubber's address
  handling is incomplete and the existing address test makes no assertions, so
  success is concrete and testable: new passing unit tests, and genuine address
  formats redacted without over-redacting ordinary text.
- **Skills match.** It needs Python, regular expressions, and pytest — all
  things I want to practice, with a fast local feedback loop (run one test
  file).
- **No blocking dependencies.** It doesn't depend on any other open issue and
  touches an isolated part of the safety layer.
- **Availability.** No one else had commented on or claimed the issue when I
  selected it.
- **Effort is realistic.** It's a bounded regex-and-tests change I can complete
  and verify locally within a good-first-issue time budget.

**Scope boundary:** I'll keep this change to address-format coverage in the PII
scrubber. Related-but-separate problems I noticed — e.g. the phone-number regex
failing on formats like `(555) 123-4567` — are out of scope and belong in their
own issue.
