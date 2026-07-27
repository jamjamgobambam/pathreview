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

## Week 8 — Reproduction

**Reproduced the bug** by running `_detect_sections()` against resume text with
leading whitespace (matching PDF-extracted formatting). Confirmed via the
repro script in issue #147:

    from ingestion.parsers.resume_parser import ResumeParser
    r = ResumeParser()
    res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
    print(res.metadata['detected_sections'])
    # Output: []  (expected: ['Education', 'Skills'])

Also ran the three failing tests named in the issue and confirmed all three
fail against current `main`:

    pytest tests/unit/test_resume_parser.py -v -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections"
    # 3 failed, 7 deselected

All three fail with `assert 0 > 0` / `assert False` — `_detect_sections()`
returns an empty list whenever the input has leading whitespace on each line,
confirming the root cause described in the issue: the section-header regex
patterns anchor to the very start of a line and don't account for indentation.