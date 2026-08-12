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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in on PR #1 during the module window. I shared the draft PR in Slack
after finishing the fix, but no peer or mentor comment landed before I had to move it
to ready-for-review to meet the Week 9 deadline. Per the Summer '26 note that reviewer
feedback isn't guaranteed this term, I'm recording this as "no feedback received"
rather than treating it as a gap in my process.

**How you responded:**
N/A — nothing to respond to. I did do my own adversarial pass in place of a reviewer:
before opening the PR I ran `git stash` to diff my change against the unmodified branch
specifically to prove I hadn't introduced new lint/type/test failures, and wrote the
pre-existing-failure findings into the PR's "Notes for Reviewers" section so that if a
review had come in, the reviewer wouldn't have had to rediscover them themselves.

---

### Reflection

**What was harder than you expected?**
Not the fix itself — the four-line regex change was genuinely the easy part, and I had
it working within the first session of Week 9. What actually cost time was the
pre-commit hook rejecting a clean, tested commit because of `mypy` failing on eleven
test functions I had never touched. I expected "implement the fix" to be the hard part
of this module; it turned out to be "figure out whether this rejection is my problem to
fix." Tracing it to a real mismatch between `.pre-commit-config.yaml` (no `tests/`
exclusion) and the `Makefile`'s own `typecheck` target (which explicitly excludes
`tests/`) took longer than writing the actual bug fix, and there was no way to know that
going in — PLAN.md's "risks" section named threshold/whitespace edge cases, not "the
repo's own tooling will disagree with itself."

**What did you learn about working in a large codebase?**
That "my change is correct" and "my change is mergeable" are two different bars, and
the gap between them is usually pre-existing mess that has nothing to do with your
issue. On a solo project, a failing type check or a stale lint rule is something I'd
just fix on the spot. Here, fixing it would have meant expanding a four-line resume-
parser bugfix into a dozen lines of unrelated test-file annotations — which is exactly
the kind of scope creep that makes a diff harder for a reviewer to evaluate for the one
thing it's supposed to do. I learned to draw a hard line at "does this failure predate
me, and does my change make it worse" — and if the answer is no on both counts, document
it and move on rather than either silently expanding scope or silently bypassing
everything with `--no-verify`.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for exactly the things that benefit from a second, tireless
pass: reproducing the issue precisely (running the exact repro string, then the exact
named tests, rather than "something similar"), writing the PLAN.md skeleton so I had a
structure to fill in rather than a blank page, and drafting commit messages/PR text in the
project's actual conventions instead of generic ones. It fell short at the one moment that
mattered most this module — deciding what to do about the mypy/pre-commit mismatch. That
required a judgment call specific to this repo's priorities (don't pad the diff, don't
skip real checks, do document transparently) that no amount of pattern-matching against
"how other people fix bugs" could make for me. AI could lay out the three options clearly;
it couldn't tell me which one this specific reviewer, in this specific course, would want
weighed how.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` as a baseline *before* writing the fix, not
after — the course materials actually recommend this and I only really internalized why
after living through the alternative: discovering a tooling gap reactively, at commit
time, instead of calmly, while writing PLAN.md's risk section. I'd also file the
`.pre-commit-config.yaml`/`Makefile` mypy mismatch as its own small issue rather than only
footnoting it in my PR notes — documenting it in my PR fixed the surprise for one
reviewer on one PR; the trap is still sitting there for the next contributor who touches
any test file in this repo.

**What are you most proud of from this module?**
Not the fix — the four-line regex change is almost too small to be proud of on its own.
I'm proud of the paper trail: JOURNAL.md and PLAN.md together mean anyone (a reviewer, a
future me, a grader) can reconstruct exactly why I made every non-obvious call — why I
patched the detector instead of the extracted text, why I skipped only `mypy` and not the
whole hook chain, why two specific test failures were left alone. That habit of writing
down the *why*, not just the *what*, is the part of this module I actually expect to keep
using after the course ends.