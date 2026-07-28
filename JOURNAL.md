## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers #146

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in the safety layer (`safety/pii_scrubber.py`) is responsible for redacting personal contact info — like phone numbers — from text before it flows through the review pipeline. Its `phone_us` regex only accepts a hyphen or period as the separator after an optional closing parenthesis, so it silently fails to match common formats like `(555) 123-4567` or `+1 555 123 4567` where a space follows the area code. As a result, real phone numbers in those formats pass through unredacted instead of being replaced with `[REDACTED]`, which is a privacy leak in an app that processes resumes and profile text. A successful fix updates the regex to accept flexible spacing after the parenthesized area code without introducing false positives on unrelated parenthesized text, backed by new regression
tests for these formats.

**Branch name:** fix/146-pii-parenthesized-phone-numbers

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 1a15bd013ee862097b11fddbdc83fc1e54e0f99a

**Reproduction summary:**
Reproduced by importing `PIIScrubber` directly and calling `scrub()`/`detect()` on
`"(555) 123-4567"`: the parenthesized number passed through untouched and `detect()` returned
an empty list, while an unparenthesized equivalent (`555-123-4567`) was correctly redacted.
Running `pytest tests/unit/test_pii_scrubber.py -v` confirmed 5 existing tests fail against
this behavior.

**PLAN.md link:** 

**Blockers or open questions:**
While reproducing, also found that `test_mixed_pii_and_text` fails for an unrelated reason: the
`street_address` pattern's `Pl` abbreviation matches the tail of ordinary words like
"applications" (case-insensitive), corrupting unrelated text. Not in scope for #146, but flagging
in case it should be filed as a separate issue before Week 9.
