# Module 3 Journal

## Week 7

- Issue selected: #111 — Add property-based tests for the PII scrubber
- Summary: I worked on improving the PII scrubber by tightening its phone and address detection logic and adding Hypothesis-based property tests to cover valid PII redaction behavior.
- Branch: `issue-111-pii-scrubber-tests`
- Validation: Ran `C:/Python313/python.exe -m pytest tests/unit/test_pii_scrubber.py -q` and got `27 passed`.
- Notes: The work focused on making the scrubber more reliable for common phone formats and on adding property-based coverage for non-PII preservation and PII redaction.

## Week 8

- Goal: Reproduce the issue locally, finalize the solution plan, and produce a short Loom walkthrough that explains the fix.
- Reproduction: verified PII scrubber behavior with `pytest tests/unit/test_pii_scrubber.py -q` and identified regex weaknesses for US phone formats and street address detection.
- Plan document: added `WEEK8_PLAN.md` with issue summary, root cause, proposed fix, and test plan.
- Next steps: implement any remaining cleanup, run `make check && make test-unit`, and record a ≤2 minute Loom walkthrough showing the issue, fix, and validation.
