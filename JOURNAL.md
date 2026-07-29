## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/147)

**Issue title:** Resume section detection fails on text with leading whitespace
 

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue talks about the whitespace detection on resume where it is not appropriate. It appears that when working with PDF's, if the output shows inappropraotely whitespaces in education, experience, and certificates. the section-header regex patterns are anchored to ^ / \n without allowing for leading whitespace, so indented resume text (common from PDF extraction) never matches. I'll be checking _strip_markdown() for the same issue while I'm in there. 

**Branch name:** fix/147-resume-parser-index-error

**Setup confirmation:** [Requirement	Minimum	Check command
Git	2.39	git --version
Python	3.11	python --version
Node.js	18	node --version
npm	9	npm --version
Docker	24	docker --version
Docker Compose	2.20	docker compose version
RAM	8 GB	—
Free disk	20 GB	— ] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

---

## Week 8 — Reproduce the Issue

**How I reproduced the issue:**
Ran a Python script locally that called `_detect_sections()` directly with resume text where each section header had 2 leading spaces — simulating real PDF extraction output:

```python
from ingestion.parsers.resume_parser import ResumeParser
parser = ResumeParser()
text = """
  Education
  B.S. Computer Science, 2022

  Experience
  Software Engineer at Acme Corp

  Skills
  Python, JavaScript
"""
result = parser._detect_sections(text)
print("Detected sections:", result)
# Output: []
```

**What I actually saw:**
`Detected sections: []` — an empty list. None of the three section headers were detected despite being present in the text. When I removed the leading spaces, all three sections were correctly detected. The bug is reliably reproducible.

**Root cause (exact location):**
`ingestion/parsers/resume_parser.py` lines 135–138 — the 4 regex patterns anchor matches to `^` or `\n` with no `\s*`, so any leading whitespace before a section header causes it to be silently skipped.

**Approach — files I will touch:**
- `ingestion/parsers/resume_parser.py` — add `\s*` after `^` and `\n` in all 4 patterns in `_detect_sections()`
- `tests/unit/test_resume_parser.py` — convert the existing `xfail` test to a passing test after the fix

**Riskiest part:**
`_strip_markdown()` has the same `^` anchoring issue for indented markdown headers (e.g. `  # Education`). Will check whether that edge case needs to be in scope.

**Commit documenting reproduction:**
Added a failing test `test_detect_sections_with_leading_whitespace` marked `@pytest.mark.xfail` to `tests/unit/test_resume_parser.py`. The test runs as XFAIL, proving the bug is real and showing exactly where the fix needs to go.

**Branch URL:** https://github.com/lavgolla/pathreview/tree/fix/147-resume-parser-index-error