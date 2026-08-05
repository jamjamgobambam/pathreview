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

---

## Week 9 — PR Submission

**PR link:** https://github.com/ascherj/pathreview/pull/232

**PR title:** fix(ingestion): allow leading whitespace in resume section detection

**What the PR does:**
PDF-extracted resume text commonly has leading whitespace on each line. The 4 regex patterns in `_detect_sections()` were anchored to `^` and `\n` with no `\s*`, so section headers like `  Education` were silently skipped and the method returned `[]`. This PR adds `\s*` to all 4 patterns and applies the same fix to `_strip_markdown()` for indented markdown headers.

**Files changed:**
- `ingestion/parsers/resume_parser.py` — regex fix in `_detect_sections()` and `_strip_markdown()`
- `tests/unit/test_resume_parser.py` — new test `test_detect_sections_with_leading_whitespace`

**Checks:**
- [x] `make test-unit` — 11/11 resume parser tests pass
- [x] `make lint` — clean on all touched files (ruff + black)
- [x] `make typecheck` — no issues on touched files
- [x] Pre-existing failures in other modules are unrelated to this PR

**Branch URL:** https://github.com/lavgolla/pathreview/tree/fix/147-resume-parser-index-error

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [Y] No — reviewer feedback is not provided in Summer 2026

**Summary of feedback:**
No review came in. Per course instructions, peer/maintainer review is not a feature in Summer 2026 and will be expanded in Fall 2026.

**How you responded:**
N/A — no feedback to respond to. PR #232 remains open at https://github.com/ascherj/pathreview/pull/232.

---

### Reflection

**What was harder than you expected?**
Understanding the full shape of the codebase before touching anything was harder than I expected. I assumed the bug would be isolated to one function and easy to find, but I had to trace through `parse()` → `_parse_pdf()` → `_detect_sections()` to understand why section detection was failing silently — it never raised an error, it just returned an empty list. Silent failures in parsing pipelines are harder to debug than exceptions because there is no stack trace pointing you to the problem. I also did not anticipate that the same anchoring issue existed in `_strip_markdown()`, so I had to scope the fix wider than originally planned.

**What did you learn about working in a large codebase?**
The biggest difference from building my own project is that you cannot hold the whole codebase in your head. In my own projects I know why every line exists. Here, I had to build trust incrementally — reading existing tests to understand expected behavior before I changed anything, and running `make test-unit` frequently to catch regressions I did not anticipate. I also learned that pre-existing lint failures in unrelated files create noise that makes it hard to know whether your own changes are clean. Scoping checks to only the files I touched (`ruff check ingestion/parsers/resume_parser.py`) was more useful than running `make check` against the whole repo.

**How did AI tools help — and where did they fall short?**
AI was most useful for two things: quickly locating the exact lines where the bug lived (lines 135–138 in `resume_parser.py`) and generating the reproduction script that confirmed the bug reliably before I wrote any fix. That saved significant time compared to reading through the entire file manually. Where AI fell short was in understanding project conventions — it could not tell me without reading `docs/CONTRIBUTING.md` that commit messages needed a scope like `fix(ingestion):`, or that `make check` errors in unrelated files were pre-existing and not my responsibility to fix. I had to read the docs myself and make that judgment call.

**What would you do differently if you started over?**
I would read `docs/CONTRIBUTING.md` on day one, before writing a single line of code. I spent time cleaning up lint issues near the end that I could have avoided by knowing the conventions upfront. I would also write the failing `xfail` test first, before attempting the fix — I did eventually do this, but adding the test after the fact made the commit history slightly awkward. Test-first would have made the reproduction step and the fix step cleaner as separate commits.

**What are you most proud of from this module?**
I am most proud of correctly identifying and fixing the `_strip_markdown()` edge case, which was not mentioned in the original issue. The issue only described the `_detect_sections()` bug, but while reading the code I noticed that `_strip_markdown()` had the same `^` anchoring problem for indented markdown headers. Catching that secondary bug and fixing it in the same PR — without being told to — is the kind of thing that makes a contribution genuinely useful rather than just technically correct.