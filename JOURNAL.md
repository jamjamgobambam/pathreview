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
