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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/josezindia/pathreview/commit/0066214bd2f7dd607bc115e89cb7d1561a27dcd4

**Reproduction summary:**
Reproduced the bug by running `_detect_sections()` against resume text with
leading whitespace (matching PDF-extracted formatting), using the repro
script from issue #147:

    from ingestion.parsers.resume_parser import ResumeParser
    r = ResumeParser()
    res = r.parse('\n    John Smith\n    john@example.com\n\n    Education:\n    - B.S. Computer Science\n\n    Skills: Python\n')
    print(res.metadata['detected_sections'])
    # Output: []  (expected: ['Education', 'Skills'])

Confirmed `detected_sections` returns `[]` instead of the expected sections.
Also ran the three named failing tests and confirmed all three fail against
current `main`:

    pytest tests/unit/test_resume_parser.py -v -k "test_parse_single_column_resume_text or test_parse_resume_no_work_experience or test_detect_sections"
    # 3 failed, 7 deselected

All three fail with `assert 0 > 0` / `assert False` — confirming the root
cause described in the issue: the section-header regex patterns in
`_detect_sections()` anchor to the very start of a line and don't account
for leading indentation.

**PLAN.md link:** https://github.com/josezindia/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Need to confirm during implementation whether `_strip_markdown()` already
strips leading whitespace before `_detect_sections()` runs on the markdown
path — if so, the fix may behave differently for PDF vs. markdown input and
I'll need to test both paths separately.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `_detect_sections()` — added `\s*` after each regex
anchor to allow leading whitespace before section headers. All three tests
named in issue #147 now pass, and no previously-passing tests broke.

**Next steps:**
Run `make check` and `make test-unit` for a full before/after comparison,
write the PR description, and open a draft PR for feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/604

**Branch:** fix/147-resume-section-whitespace

**What you built:**
Fixed section header detection in the resume parser so it correctly finds
sections (Education, Skills, etc.) in text with leading whitespace, which is
common in PDF-extracted resumes. The fix adds `\s*` to the regex patterns in
`_detect_sections()` so headers are matched regardless of indentation.

**Tests added or updated:**
No new tests were added — the fix makes three existing tests pass
(`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`,
`test_detect_sections` in `tests/unit/test_resume_parser.py`), with no
regressions in previously-passing tests.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both confirmed clean on the changed file; pre-existing unrelated failures
elsewhere in the codebase documented in the PR description)


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback arrived — the course confirmed reviewer feedback isn't
a feature this term (Summer 2026). I did post my draft PR in the #ai-engineers
Slack channel asking for peer feedback but did not receive any responses
before this deadline.

**How you responded:**
N/A — no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
Environment setup took far longer than I expected — not because of the
actual issue fix, but because of a chain of unrelated failures: Docker
wasn't installed at all, Postgres was mapped to a non-default port (5433
instead of 5432) that I had to notice from `docker compose ps` output, and
the ChromaDB container crashed on every startup because its entrypoint
script force-reinstalled `chroma-hnswlib` and pulled in NumPy 2.0, which
broke on `np.float_` being removed. None of that was related to my actual
issue — it was just getting the project to run at all. I didn't expect
"getting the app running" to take longer than diagnosing and fixing the
actual bug.

**What did you learn about working in a large codebase?**
The actual code change was tiny — four regex patterns, one word (`\s*`)
added four times — but confirming it was safe took real effort: running the
full test suite before and after, checking for regressions, and figuring
out which of the pre-existing failing tests were related to my change versus
just pre-existing noise in the codebase (I found 53 failing tests and 182
lint errors that had nothing to do with my issue). In a codebase you own,
you'd just fix things as you notice them. In someone else's production
codebase, scope discipline matters — I found a second bug in
`_strip_markdown()` with the same root-cause pattern (regex anchored to `^`
without accounting for whitespace) while investigating, but left it alone
since it wasn't part of my issue, rather than expanding the PR.

**How did AI tools help — and where did they fall short?**
AI was most useful for fast diagnosis under uncertainty — reading stack
traces (SQLAlchemy/asyncpg connection errors, the NumPy AttributeError) and
narrowing down root causes quickly instead of me googling each error
individually. It was also useful for keeping the regex fix minimal and
explaining tradeoffs (e.g., why `\s*` was the right scope, not a rewrite).
Where it fell short: it couldn't actually see my terminal state, so several
times I had to paste back real output before it could correct a wrong
assumption (e.g., assuming a fix had been applied when it hadn't, or
guessing at a file path). It also has no way to know undocumented,
project-specific details on its own — like the Docker port mapping or which
Slack channel to post in — I had to supply that context directly.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` for a full baseline immediately
after environment setup, before even reading the issue in detail. I only
did this at the start of Week 9, but having that baseline earlier would have
let me identify the "182 pre-existing lint errors, 53 pre-existing test
failures" context from day one instead of discovering it midway through
implementation.

**What are you most proud of from this module?**
Getting the local environment fully working despite three unrelated,
stacked failures (missing Docker, wrong Postgres port, and a genuinely
broken NumPy pin in the ChromaDB image) that had nothing to do with my
actual issue. It would have been easy to get stuck or give up before ever
reaching the code I was supposed to fix, and instead I diagnosed each
layer systematically until the whole stack came up clean.