## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/147)]

**Issue title:** [Resume section detection fails on text with leading whitespace]

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

[This issue is a strong fit for where I am in the pathreview project. I can clearly explain the problem in my own words: _detect_sections() in resume_parser.py anchors its section-header regex patterns (^Experience, \nExperience) to the very start of a line, but PDF-extracted text frequently preserves leading whitespace from the original layout — so a header like "Experience" comes through as " Experience" and never matches, leaving detected_sections empty even for well-structured resumes. This is a Tier 1 issue: it's self-contained, lives in a single function within one file, and doesn't require me to reason about how multiple modules or services interact — which makes it a realistic starting point rather than a stretch assignment. I've located the relevant code and the corresponding test file, and I understand the surrounding context well enough to sketch a fix (loosening the regex anchors or normalizing leading whitespace per line before matching) without needing to research the broader codebase first. Given the narrow scope — a regex/whitespace fix plus one new test case covering indented headers — I estimate this comfortably fits within the 3–6 hour range expected for a Tier 1 issue, leaving margin within the Week 8–9 window alongside my other coursework.]

**Problem summary:**
[In resume_parser.py, the _detect_sections() function relies on regex patterns that require section headers to begin at the very start of a line, with nothing preceding them. This assumption fails for text extracted from PDFs, since PDF-to-text extraction frequently retains leading whitespace (spaces or tabs) from the original document layout, so headers like "Experience" or "Education" end up indented rather than flush-left. As a result, none of the section patterns match, and detected_sections returns empty even for resumes that clearly contain well-formed sections. A successful fix would make the header-matching logic tolerant of leading whitespace — either by adjusting the regex patterns or normalizing each line before matching — so that section detection works reliably regardless of whether the source text came from a PDF or another format.]

**Branch name:** [fix/147-resume-parsing-error]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [to be filled in after push — see this commit]

**Reproduction summary:**
Ran the exact snippet from the issue (`ResumeParser().parse(...)` on a string with
leading whitespace on every line) and confirmed `detected_sections` comes back `[]`
instead of `['Education', 'Skills']`. Also ran the three named tests
(`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections` in `tests/unit/test_resume_parser.py`) — all three fail with
`AssertionError` for the same reason: their resume fixtures are Python triple-quoted
strings, which carry the same kind of per-line leading indentation as PDF-extracted
text, so `_detect_sections()`'s regex patterns (anchored directly to `^`/`\n` with no
whitespace tolerance) never match.

**PLAN.md link:** [to be filled in after push]

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
None yet — root cause is confirmed and isolated to a single function
(`_detect_sections` in `ingestion/parsers/resume_parser.py`). Main open question
going into the fix is whether loosening the regex to tolerate leading whitespace
could introduce false positives (e.g. a section-name word appearing mid-sentence
on an indented line) — noted as a risk in PLAN.md.
