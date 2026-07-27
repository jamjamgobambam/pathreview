## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The resume parser detects section headers (like "Education" or "Skills") using
regex patterns that only match when a header starts at the very beginning of a
line, with no leading whitespace. PDF-extracted resume text frequently has
indented lines, so real-world input causes the parser to find zero sections
even when they're clearly present. This affects `_detect_sections()` in
`ingestion/parsers/resume_parser.py`, and breaks downstream logic that depends
on knowing which sections a resume contains. A fix should let the header
patterns match regardless of leading whitespace/indentation on each line.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/josezindia/pathreview/commit/0066214bd2f7dd607bc115e89cb7d1561a27dcd4

**Reproduction summary:**
Reproduced the bug by running `_detect_sections()` against resume text with
leading whitespace (matching PDF-extracted formatting), using the repro
script from issue #147:

    from ingestion.parsers.resume_parser import ResumeParser
    r = ResumeParser()
    res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
    print(res.metadata['detected_sections'])
    # Output: []  (expected: ['Education', 'Skills'])

Confirmed `detected_sections` returns `[]` instead of the expected sections.
Also ran the three named failing tests and confirmed all three fail against
current `main`:

    pytest tests/unit/test_resume_parser.py -v -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections"
    # 3 failed, 7 deselected

All three fail with `assert 0 > 0` / `assert False` — confirming the root
cause described in the issue: the section-header regex patterns in
`_detect_sections()` anchor to the very start of a line and don't account
for leading indentation.

**PLAN.md link:** https://github.com/josezindia/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Need to confirm during implementation whether `_strip_markdown()` already
strips leading whitespace before `_detect_sections()` runs on the markdown
path — if so, the fix may behave differently for PDF vs. markdown input and
I'll need to test both paths separately.