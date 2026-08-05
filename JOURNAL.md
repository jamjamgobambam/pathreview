## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace
 #147

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug lies in _detect_sections() in resume.py. Section-header detection only matches headers at the start of a line, so when a PDF adds leading whitespace (indentation) before a header, it's missed—causing the parser to conclude the resume has no sections at all. The fix needs to recognize indented text as a valid header while still not treating every indented line as one.

**Selection Reasoning:**
I chose this issue because this falls within my limited scope since I have never done big codebase changes or fixes. In the past, I have taken python classes that taught the basics of regex and cleaning data with abnormalities like whitespaces. Data cleaning is also a relevant topic in my job, so I feel that it is a topic I am well versed with.

**Branch name:** fix/147-resume-section-detection-fails-on-text-with-leading-whitespace

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/angstef24/pathreview/commit/b8d7682

**Reproduction summary:**
I called `ResumeParser._detect_sections()` directly with two versions of the same resume text — one flush-left, one with each line indented (mimicking how some PDFs extract text with a left margin). The flush-left version correctly returned `['Experience', 'Skills', 'Education']`, while the indented version returned `[]`. This confirmed the existing `tests/unit/test_resume_parser.py::test_detect_sections` test, which also fails today (`assert 0 > 0`) because its sample text is indented — the regex patterns in `_detect_sections()` anchor directly on `^`/`\n` with no allowance for leading whitespace.

**PLAN.md link:** https://github.com/angstef24/pathreview/blob/fix/147-resume-section-detection-fails-on-text-with-leading-whitespace/PLAN.md

**Blockers or open questions:**
Still need to confirm whether real-world PDF extraction ever uses tabs or non-breaking spaces for indentation (vs. plain spaces), which would affect how permissive the fixed regex needs to be.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix from PLAN.md is implemented. I rewrote the pattern list in `_detect_sections()` (`ingestion/parsers/resume_parser.py`) so the header regexes use `^[ \t]*`/`\n[ \t]*` instead of anchoring directly on `^`/`\n`, which lets indented and PDF-extracted headers (e.g. `    Education:`) match.

Completed PLAN.md sub-tasks:
1. Fixed `_detect_sections()` to allow leading whitespace before a header.
2. Confirmed the three originally-failing tests now pass: `test_detect_sections`, `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`.

**Next steps:**
Add/update unit tests covering the indentation fix (per PLAN.md's sub-tasks 3–4: an indented-header case and a guard against misdetecting indented body text as a header), run `make check` on the changed files and fix any issues, open a draft PR against pathreview and request peer feedback in Slack, fill in the PR template, then mark it ready for review and add Check-in 2.

**Blockers:**
No major blockers. It may take some time to get the PR reviewed. Note: `make test-unit` has ~50 pre-existing failures across unrelated modules (`review_service`, `pii_scrubber`, `skill_extractor`, etc.) that exist on a clean checkout before my changes. My changes don't touch those; I confirmed the resume-parser suite goes from 5 failing to 2 failing, where the remaining 2 (`test_parse_markdown_resume`, `test_strip_markdown_syntax`) are pre-existing failures in `_strip_markdown`, unrelated to issue #147.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/723

**Branch:** fix/147-resume-section-detection-fails-on-text-with-leading-whitespace

**What you built:**
Updated the four regex patterns in `_detect_sections()` (`ingestion/parsers/resume_parser.py`) to allow optional leading whitespace (`[ \t]*`) before a section header, so resumes with indented/PDF-extracted headers (e.g. `    Experience`) are correctly detected instead of returning no sections at all.

**Tests added or updated:**
Added `test_detect_sections_with_leading_whitespace` and `test_detect_sections_does_not_match_indented_body_text` to `tests/unit/test_resume_parser.py` — one confirms indented headers are detected, the other guards against indented body text that merely mentions a header word being misdetected as one.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
(Both "pass" in the sense that my changes introduce no new failures beyond this repo's pre-existing baseline — documented in the PR description: `make test-unit` goes from 53 failing/375 passing to 50 failing/380 passing, and `make lint` goes from 182 to 177 pre-existing errors; `make typecheck` is unaffected.)

**Draft PR feedback received from:** none yet

**Blockers or open questions:**
None currently. The `_strip_markdown()` header-stripping bug (same "no leading whitespace" root cause, different method) is still unfixed and causing 2 pre-existing test failures — flagged in the PR as a possible follow-up issue, out of scope for #147.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review
(Su26 note: reviewer feedback isn't a feature this term, so there's nothing to check the PR for beyond confirming it — no comments have come in on PR #723.)

**Summary of feedback:**
No review came in.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
The actual regex fix was the easy part with most of the friction was environment and process. Getting Docker Desktop running (installing via Homebrew, then realizing it had to actually be launched once before `docker compose` even existed as a command) took longer than the bug fix itself. I also didn't understand `origin` vs `upstream` going in, and I got nervous the first time a push happened, thinking it was going to the real project, before realizing `origin` was my own fork the whole time. The other surprise was how much of my time went into pre-commit hooks failing on code I hadn't touched (a missing `raise ... from e` and untyped test functions that predated my change) rather than on my actual fix.

**What did you learn about working in a large codebase?**
The biggest shift was realizing a codebase doesn't need to be fully green for a contribution to be valid. This repo had 53 pre-existing failing tests and 182 pre-existing lint errors before I changed anything. The bar is "don't make it worse," not "fix everything you see," which is a different mindset than a solo project where you'd expect a clean test run. I also learned that the same bug pattern can hide in more than one place. `_strip_markdown()` had the identical "no leading whitespace" flaw as `_detect_sections()` — and part of the job is staying disciplined about what's actually in scope for the issue instead of fixing everything you notice.

**How did AI tools help — and where did they fall short?**
AI was most useful for diagnosing failures quickly like figuring out why a pre-commit hook failed, tracing a test failure back to its root cause across files, and reproducing the bug directly instead of guessing. It also helped me get PLAN.md, JOURNAL.md, and the PR description into the format the course/repo actually wanted. The only place it really fell short for me was that it couldn't install Docker Desktop or click through its setup for me.

**What would you do differently if you started over?**
I'd get the fork/branch/remote mental model straight before starting, instead of mid-way through Week 8. I'd also read CONTRIBUTING.md's commit message convention before my first commit rather than after several were already pushed, I ended up with commits that don't match the required `type(scope): description` format.

**What are you most proud of from this module?**
Reproducing a bug reliably before touching any code, and proving with numbers (53→50 failing, 182→177 lint errors) that my fix didn't regress anything else in a codebase I'd never seen before Week 7. That verification step felt like the real skill this module was trying to teach, more than the one-line regex change itself.
