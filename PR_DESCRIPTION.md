<!--
Note: on a typical open-source contribution, this content wouldn't exist as
its own committed file — it would just be pasted directly into the PR body
field when opening the pull request on GitHub, and this file wouldn't be
part of the repo at all. Keeping it here as a committed artifact for this
course project's process documentation, alongside PLAN.md and JOURNAL.md.
-->

Title: fix: tolerate leading whitespace in resume section headers (#147)

## Summary

I fixed issue #147: resume section detection was failing to recognize section headers ("Experience:", "Education:", "Skills:") whenever they had leading whitespace in front of them, which turns out to be a common artifact of PDF-extracted text and indented markdown resumes. `_detect_sections()`'s four regex patterns and `_strip_markdown()`'s header-stripping regex were all anchored directly to `^`/`\n` with zero tolerance for leading spaces or tabs, so any indented header was silently skipped and `detected_sections` came back empty — even when the sections were obviously there to a human reader. I added `[ \t]*` tolerance to all five regexes so indented headers get detected/stripped the same as flush-left ones, and I specifically tested that this doesn't introduce false positives for section keywords that show up indented mid-sentence (e.g. inside a bullet point).

## Issue

Closes #147

## Changes

Root cause: `_detect_sections()` and `_strip_markdown()` each build their own line-start regex (`^{keyword}...`, `\n{keyword}...`, and `^#+\s+` respectively), and both anchor directly to the start of the line with no allowance for whitespace before it. Real resume text commonly has that leading whitespace — PDF text extraction adds it as a layout artifact, and indented markdown source has it structurally — so on indented input, the anchor never matches, the header is silently skipped, and `detected_sections` comes back empty even though a human reader can see the sections clearly.

- `ingestion/parsers/resume_parser.py` — added `[ \t]*` leading-whitespace tolerance to the 4 regex patterns in `_detect_sections()` (~lines 134-138) and to `_strip_markdown()`'s header-removal regex (~line 102)
- `tests/unit/test_resume_parser.py` — added `test_detect_sections_tabs_and_no_false_positive`, covering tab-indented headers plus a negative case (an indented bullet that just mentions a section keyword mid-sentence must NOT be detected as a header). `test_parse_pdf_with_indented_sections`, added during Week 8 reproduction, verifies the fix through the PDF ingestion path specifically, since none of the tests named in the original issue exercised that code path

## Testing

- [x] Unit tests pass (`make test-unit`)
- [ ] Integration tests pass (`make test-integration`) — not applicable, this change has no integration-layer surface
- [ ] Linter passes (`make lint`) — repo has pre-existing lint debt unrelated to this change; see Notes for Reviewers
- [ ] Type checker passes (`make typecheck`) — pre-existing repo-wide crash unrelated to this change; see Notes for Reviewers
- [x] New/updated tests cover the changes

**Reproduce the original bug (before the fix):**

1. Check out `main`
2. In a Python shell:

   ```python
   from ingestion.parsers.resume_parser import ResumeParser
   parser = ResumeParser()
   text = "John Doe\n\n    Experience:\n    Senior Developer\n\n    Skills: Python\n"
   print(parser._detect_sections(text))
   ```

3. Observe: `[]` — both sections are present in the text but neither is detected, because of the 4-space indent.

**Verify the fix (on this branch):**

1. Check out `fix/147-resume-section-whitespace`
2. Run the same snippet above
3. Expected: `['Experience', 'Skills']`
4. `.venv/bin/pytest tests/unit/test_resume_parser.py -v` — expect 12 passed, 0 failed
5. To confirm no regressions elsewhere: `.venv/bin/pytest tests/unit -m unit` — expect 48 failed / 382 passed, the exact same pre-existing-failure set as `main` (see Notes for Reviewers)

## Screenshots / Demo

N/A — backend parsing fix, no UI surface. The observable behavior is the `_detect_sections()` return value shown in the Testing steps above.

## Notes for Reviewers

- **Pre-existing, unrelated failures:** `make check`'s typecheck step currently crashes on `main` too — I confirmed this with `git stash` before making any changes, so it predates this branch. Root cause: `pyproject.toml` pins `numpy>=1.26.0` with no upper bound, a fresh install today resolves to numpy 2.5.1, and its bundled stubs need Python 3.12+ syntax, but `[tool.mypy]` still targets `python_version = "3.11"`, so mypy crashes immediately. I didn't fix this here — bumping the mypy target to unblock it surfaces 103 pre-existing type errors across 26 unrelated files, well outside this issue's scope (confirmed with a tech fellow that leaving it out is the right call). Happy to file it as a separate issue if useful.
- The full unit suite has 48 pre-existing failures across ~15 unrelated modules that this PR doesn't touch (baseline captured in `JOURNAL.md`/`PLAN.md` on this branch).
- I deliberately didn't extend this fix to dash-bullet-style headers (e.g. `- Experience`) or hyphenated compound words like "Experience-driven..." — both are pre-existing, separate limitations outside this issue's whitespace-specific scope. Documented both in `PLAN.md`'s Edge Cases section rather than trying to fix them here.
