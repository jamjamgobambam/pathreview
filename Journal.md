## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146#

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** Tier 1

**Problem summary:**
The personal information scrubbery in pii_scrubber.py is not redacting phone numbers with a parenthesized beginning format. The scrub is not redacting and the format is not being detected. A successful fix would lead to the parenthesized format of phone numbers being detected and redacted from text. This file is in the safety folder, but I cannot find reference to it outside the test suite. So I assume it is not integrated into the project and not affecting other files. 

**Branch name:** fix/146-pii-scrubber-phone-number

**Setup confirmation:** Yes, app runs locally at localhost:5173.

**Cohort ledger:** Yes, issue was added to cohort ledger.

## "Is this right for me?" Checklist:
### Tier Fit
- Is this an appropriate tier for my experience? Yes, because I have not done open source contributions, and I have fixed similar bugs before.

### Codebase Readiness
- **Relevant function/module found:** pii_scrubber.py
- **Rough implementation plan:**
  1. Run relevant tests to replicate the bug.
  2. Read the file.
  3. Identify the code likely responsible.
  4. Propose the fix.
  5. Test the fix
  6. Run entire test suite. 
  7. Repeat if issue is not reolved.

- **Relevant test files:**
- test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text in tests/unit/test_pii_scrubber.py

### Scope & Time
- **Others already working on it?** When I first went to claim it no, but now there are many others working on it.
- **Estimated time:** 2-3 hrs
- **Can I finish before the deadline?** Yes, seems like a minor issue. I have solved similar bugs before.
- **Dependencies/blockers:** None
