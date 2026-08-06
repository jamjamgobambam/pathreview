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

**Reproduction commit link:** [f0b05ed](https://github.com/prkapoor-seas/pathreview/commit/f0b05ed887d639b721dd73c29b7989a7a4e2f696)

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

**PLAN.md link:** [PLAN.md](https://github.com/prkapoor-seas/pathreview/blob/fix/147-resume-parsing-error/PLAN.md)

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
None yet — root cause is confirmed and isolated to a single function
(`_detect_sections` in `ingestion/parsers/resume_parser.py`). Main open question
going into the fix is whether loosening the regex to tolerate leading whitespace
could introduce false positives (e.g. a section-name word appearing mid-sentence
on an indented line) — noted as a risk in PLAN.md.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented PLAN.md steps 1–3: loosened the four regex patterns in
`_detect_sections()` to tolerate optional leading whitespace (`[ \t]*`) between
the line anchor and the section name, and added two regression tests
(`test_detect_sections_with_leading_whitespace`, matching the issue's exact
repro case, and `test_detect_sections_with_tabs_and_inconsistent_indentation`
for tab-indented and mixed-depth headers). Confirmed via `make test-unit` that
this fixes all 3 tests named in the issue and introduces zero new failures
(53 failed/375 passed baseline → 50 failed/380 passed). Also ran `make check`
across the full repo to document the pre-existing failure baseline (177 lint
errors, 5 typecheck errors — none in the files this PR touches). Committed as
`b40295b` on `fix/147-resume-parsing-error` (confirmed not on `main`).

**Next steps:**
Push the branch, open the PR against upstream with the drafted description
(root cause, changes, before/after test counts, pre-existing-failure notes),
and record the optional walkthrough video.

**Blockers:**
Lost time to environment issues unrelated to the actual bug: the dev venv's
SQLAlchemy install was corrupted (a `FileNotFoundError` on a missing Cython
extension file), and `make setup`'s `pre-commit install` step hung
indefinitely for reasons still unclear. Both are resolved now — `make
test-unit` and `make check` run cleanly.

---

### Check-in 2 (end of week)

**PR link:** [#577](https://github.com/ascherj/pathreview/pull/577)

**Branch:** `fix/147-resume-parsing-error`

**What you built:**
Loosened `_detect_sections()`'s regex patterns in `ingestion/parsers/resume_parser.py`
to allow optional leading whitespace between the line anchor and the section
name, so indented section headers (as commonly produced by PDF text
extraction) are detected instead of silently producing an empty
`detected_sections` list.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — added `test_detect_sections_with_leading_whitespace`
(the issue's exact repro case) and `test_detect_sections_with_tabs_and_inconsistent_indentation`
(tab indentation, headers at different depths in the same document). Also added
missing mypy type annotations across the file's existing test functions and a
`# type: ignore[arg-type]` on two tests that intentionally pass invalid types
to test runtime validation — both needed to satisfy the pre-commit hook on
this file, unrelated to the bug itself.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
_(this codebase has substantial pre-existing failures — 177 lint errors, 5
typecheck errors, 50 failing unit tests — all documented in the PR
description; "passes" here means this change introduces zero new failures
against that baseline, confirmed by diffing failure lists before/after)_

**Draft PR feedback received from:** LittlePixels — ["Looks good!"](https://github.com/ascherj/pathreview/pull/577#issuecomment-5159954240)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No — still awaiting review

**Summary of feedback:**
PR #577 is still open. The only review activity so far is a single comment
from LittlePixels — ["Looks good!"](https://github.com/ascherj/pathreview/pull/577#issuecomment-5159954240)
— with no requested changes and no formal approval/merge action recorded.
The reviewer didn't raise any of the risks I'd flagged myself in PLAN.md
(false positives from loosening the whitespace anchor, unicode whitespace
like non-breaking spaces, possible redundancy between the `^{section}` and
`\n{section}` pattern variants under `re.MULTILINE`), so those remain
self-identified open questions rather than reviewer-driven ones.

**How you responded:**
No code changes were requested, so no follow-up commits were needed. The
PR and branch (`fix/147-resume-parsing-error`) remain as submitted in Week 9
— the fix in `ingestion/parsers/resume_parser.py`, the two new regression
tests in `tests/unit/test_resume_parser.py`, and the documented before/after
test-baseline diff in the PR description.

---

### Reflection

**What was harder than you expected?**
The actual bug fix — loosening four regex patterns to tolerate leading
whitespace — took far less time than the surrounding process. The bigger
time sink was environment breakage unrelated to the issue: a corrupted
SQLAlchemy install (`FileNotFoundError` on a missing Cython extension file)
and a `make setup` `pre-commit install` step that hung indefinitely. Neither
had anything to do with `_detect_sections()`, but both had to be resolved
before I could trust any test result. I also underestimated how much
judgment it would take to decide what "tests pass" even means in a codebase
that already has 177 lint errors, 5 typecheck errors, and 50 failing unit
tests on `main` — "passing" turned into "introduces zero new failures
against a documented baseline" rather than a clean run.

**What did you learn about working in a large codebase?**
A one-function fix rarely stays contained to one function. To get past the
pre-commit hook on the test file I touched, I had to add missing mypy type
annotations to existing test functions that had nothing to do with my bug —
otherwise the hook would block the commit on unrelated pre-existing debt.
I also learned that in a codebase with a large pre-existing failure count,
the useful signal isn't "does `make check` pass" but "did the failure list
change," which means diffing before/after output rather than trusting a
single pass/fail signal.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for structured planning and risk-spotting —
drafting PLAN.md's Map/Plan/Risks breakdown, reasoning through the
false-positive edge case (a section-name word appearing indented mid-sentence
rather than as a real header) before writing any code, and drafting the PR
description with the before/after test counts and baseline caveats spelled
out clearly. It fell short on the environment issues: diagnosing the
corrupted SQLAlchemy Cython extension and the hanging `pre-commit install`
required manual investigation (reading actual stack traces, testing
hypotheses one at a time) rather than something an assistant could reason
through from the issue description alone.

**What would you do differently if you started over?**
I'd budget explicit time for environment setup before starting the Week 8
reproduction step, instead of discovering the SQLAlchemy and pre-commit
issues mid-week and losing planning time to them. I'd also record the
walkthrough video earlier — it's still marked "not recorded yet" from Week
9 — rather than treating it as an optional last step that keeps sliding.

**What are you most proud of from this module?**
The two regression tests I added
(`test_detect_sections_with_leading_whitespace` and
`test_detect_sections_with_tabs_and_inconsistent_indentation`) are scoped
tightly to the actual bug rather than being generic coverage padding — one
mirrors the issue's exact repro case, the other guards the tab-indentation
and inconsistent-depth edge cases I identified as risks in PLAN.md before
writing the fix. Being able to point at PLAN.md's "Risks & unknowns" section
and show that both flagged risks ended up covered by a real test feels like
the most concrete evidence that the planning step actually paid off.
