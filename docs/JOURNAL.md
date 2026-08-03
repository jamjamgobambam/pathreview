## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

When resume text is extracted from PDFs or pasted with indentation, section headers such as “Experience:” often sit at the start of a line with spaces before them. In ingestion/parsers/resume_parser.py, _detect_sections() matches headers only when they appear flush at the beginning of a line, so those indented headers are never recognized. Parsing still returns the full resume text, but metadata["detected_sections"] stays empty, which breaks expectations in the resume parser tests and any flow that relies on knowing which sections were found. A successful fix would allow optional leading whitespace on each line in those patterns so common sections are detected correctly and metadata lists them as intended.

**Branch name:**fix147-Resume-section-detection-fails-on-text-with-leading-whitespace 

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/8d7d12f414e3ffa7e3b22c8d7ff71c2c62e0ac3b

**Reproduction summary:**
I imported ResumeParser from ingestion.parsers.resume_parser and called parse() with the indented sample resume string from issue #147. metadata["detected_sections"] was [], matching the reported bug: section headers with leading whitespace are not detected.

**PLAN.md link:** https://github.com/JJC3321/pathreview/blob/fix/147-Resume-section-detection-fails-on-text-with-leading-whitespace/docs/plan.md

**Blockers or open questions:**
None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Completed steps 1–5 from PLAN.md for issue #147. Confirmed reproduction: `test_detect_sections` failed because indented headers (leading spaces before `Experience:`, `Education:`, `Skills:`) did not match. Updated all four regex patterns in `_detect_sections` (`ingestion/parsers/resume_parser.py`) to allow optional `\s*` after `^` and `\n`. Re-ran the resume parser unit tests: `test_detect_sections` passes, and flush-left fixtures (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`) still pass. Verified end-to-end via `ResumeParser.parse()` on the indented sample — `metadata["detected_sections"]` now returns `['Experience', 'Education', 'Skills']`. Manually checked edge cases: tabs and multiple leading spaces match; mid-line headers like `See Experience: below` do not.

**Next steps:**

Commit and push the fix on branch `fix/147-Resume-section-detection-fails-on-text-with-leading-whitespace`, open a PR, and run `make check` and `make test-unit` for self-review confirmation. Fill in Check-in 2 (PR link, test summary, draft feedback) once the PR is submitted.

**Blockers:**

Two pre-existing failures in `test_resume_parser.py` (`test_parse_markdown_resume`, `test_strip_markdown_syntax`) are unrelated to this fix — `_strip_markdown` does not strip `#` headers when lines are indented. They may cause `make test-unit` to report failures beyond the scope of #147; otherwise none.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/345

**Branch:** fix147-Resume-section-detection-fails-on-text-with-leading-whitespace 

**What you built:**
Updated `_detect_sections` in `ingestion/parsers/resume_parser.py` so all four section-header regex patterns allow optional leading whitespace (`\s*`) after each line-start anchor (`^` or `\n`). Indented headers common in PDF extracts and pasted text (e.g., `    Experience:`) now match the same way flush-left headers do, so `metadata["detected_sections"]` correctly lists Experience, Education, Skills, and other recognized sections instead of staying empty.

**Tests added or updated:**
No test files were changed. The existing `test_detect_sections` in `tests/unit/test_resume_parser.py` already uses an indented fixture and was used to confirm the fix; flush-left cases remain covered by `test_parse_single_column_resume_text` and `test_parse_resume_no_work_experience`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** None


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

Writing the journal and PLAN.md was harder than the code change itself. Updating the four regexes in `_detect_sections` so they allow `\s*` after `^` and `\n` took a short time once I found `ingestion/parsers/resume_parser.py`, but explaining why that change was safe — for example that mid-line text like `See Experience: below` still should not match — forced me to slow down and justify tradeoffs I would usually leave unsaid. I also spent more time than expected sorting which failures in `test_resume_parser.py` were mine versus pre-existing (`test_parse_markdown_resume`, `test_strip_markdown_syntax`), which is not something I had to do in smaller personal projects.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

I learned that the first job is navigation, not coding: start from the issue (#147), find the failing test (`test_detect_sections`), then follow it into `_detect_sections` instead of guessing where to edit. In my own projects I usually know every file; here I had to treat `ResumeParser.parse()` → metadata → `detected_sections` as a path I needed to prove before changing anything. I also learned that a small, scoped fix still has to respect existing behavior — flush-left fixtures like `test_parse_single_column_resume_text` had to keep passing even though the bug report was only about indented headers.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

AI was most useful once I already knew the fix: helping me draft the PLAN.md steps and apply the same `\s*` change consistently across all four regex patterns so I did not miss one. It fell short when I needed to understand *why* the original patterns anchored at line start — I still had to run `pytest` myself, compare `metadata["detected_sections"]` before and after on the issue’s indented sample, and decide that tabs and multiple spaces should match but mid-line headers should not. The tooling could suggest edits; verifying the edge cases and writing a clear explanation in the journal still had to come from me.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

I would pick a Tier 2 or Tier 3 issue instead of Tier 1 #147. The whitespace regex fix was a good first contribution, but it did not stretch me enough for a capstone — I finished the code early and spent more energy on documentation than on a harder technical problem. Next time I would also add or extend a unit test for the mid-line false-positive case I only checked manually, so the PR itself documented that invariant instead of leaving it in check-in notes.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]

I am most proud of learning to use AI as a partner after I had a plan, not as a substitute for understanding the bug. Reproducing the empty `detected_sections` list, writing PLAN.md, confirming the fix against the indented sample (`Experience`, `Education`, `Skills`), and opening PR #345 felt like a complete contribution loop. That process — reproduce, plan, change a small surface carefully, prove it with tests — is what I want to carry into harder issues next.
