## Week 7 — Issue selection

**Issue link:** [[Issue Link](https://github.com/ascherj/pathreview/issues/147)]

**Issue title:** Resume section detection fails on text with leading whitespace
 #147

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
_detect_sections() in resume_parser.py identifies resume sections (Education, Skills, Experience, etc.) by matching each section keyword against patterns anchored with ^ or \n, using re.MULTILINE so ^ matches at the start of every line. The bug is that these patterns expect the keyword to appear immediately at that line-start position, with no allowance for leading whitespace — so text like "    Education:" (common in PDF-extracted text, which often preserves indentation) never matches, even though re.MULTILINE is correctly making ^ check every line. As a result, detected_sections comes back empty for indented resume text, even when section headers are clearly present. A successful fix would update the patterns (e.g. adding \s* after ^/\n) so section headers are still recognized when preceded by leading whitespace, without introducing false positives. This affects the _detect_sections method in ingestion/parsers/resume_parser.py.

**Branch name:** fix/147-resume-section-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Commit](https://github.com/sumanbista/pathreview/commit/bae24b97b890eb4887684d001a1bc361cb4bdad4)

**Reproduction summary:**
Ran the exact repro script from issue #147 against indented resume text and observed `detected_sections` return `[]` instead of `['Education', 'Skills']`; confirmed the same failure via the three tests named in the issue (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`), all of which fail with `3 failed, 7 deselected`.

**PLAN.md link:** [PLAN.md](https://github.com/sumanbista/pathreview/blob/fix/147-resume-section-leading-whitespace/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**

**Reproduction steps:**
```python
from ingestion.parsers.resume_parser import ResumeParser
r = ResumeParser()
res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
print(res.metadata['detected_sections'])
```

**Observed output:** `[]`
**Expected output:** `['Education', 'Skills']`

Also confirmed via the project's own test suite — the three tests named in the issue
all fail on `main`/this branch before any fix:

```
python3 -m pytest tests/unit/test_resume_parser.py -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections" -v
```
Result: `3 failed, 7 deselected`

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: updated the four regex patterns in `_detect_sections()`
(`ingestion/parsers/resume_parser.py`) to allow leading whitespace (`[ \t]*`) between the
line anchor and the section keyword. Added `test_detect_sections_with_leading_whitespace`
covering the issue's exact reproduction case. Confirmed the three originally-failing tests
now pass, with no new regressions (two pre-existing, unrelated test failures in
`_strip_markdown` remain unchanged). Ran `make check`/local lint and type checks — `ruff`
and `black` are clean on changed files; documented a pre-existing `mypy` gap unrelated to
this fix (see PR notes). Committed the fix and opened a draft PR (#1), already shared for
peer/mentor review.

**Next steps:**
Incorporate any peer/mentor feedback from the draft PR, then mark it ready for review.
Confirm the PR's base branch is correct (currently targets my own fork's `main`; need to
verify with instructor whether it should target `ascherj/pathreview:main` instead).

**Blockers:**
None currently — flagged but not blocked by a repo tooling inconsistency (local
pre-commit `mypy` hook checks `tests/`, but `make typecheck` excludes it), documented in
the PR description rather than fixed, since it's out of scope for issue #147.

---

### Check-in 2 (end of week)

**PR link:** [PR #1](https://github.com/sumanbista/pathreview/pull/1)

**Branch:** `fix/147-resume-section-leading-whitespace`

**What you built:**
Fixed `_detect_sections()` in `ingestion/parsers/resume_parser.py` so it correctly
detects resume section headers (Education, Skills, Experience, etc.) on lines with
leading whitespace, which is common in PDF-extracted text. The fix adds an optional
`[ \t]*` between the line anchor and the section keyword in each of the four detection
regex patterns, without changing the existing anchor/suffix matching logic.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — added `test_detect_sections_with_leading_whitespace`,
using the issue's exact reproduction input, asserting `Education` and `Skills` are
detected. Confirmed the three previously-failing tests named in the issue
(`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections`) now pass, with no new regressions elsewhere in the file.

**Self-review confirmation:** [x] make check passes*  [x] make test-unit passes*
*with two documented pre-existing, unrelated failures (see PR description): a
`_strip_markdown` test issue and a local pre-commit `mypy` hook checking `tests/`
(which `make typecheck` itself excludes) — both predate this change and are unaffected
by it.

**Draft PR feedback received from:** None.

**Root cause confirmed:** `_detect_sections()` in `ingestion/parsers/resume_parser.py`
(lines 132–144). The regex patterns anchor the section keyword directly against `^`/`\n`
with no `\s*` allowance for leading whitespace, so indented lines like `"    Education:"`
never match, even though `re.MULTILINE` correctly makes `^` check every line.