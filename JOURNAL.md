## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147 

**Issue title:** Resume section detection fails on text with leading whitespace #147

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `_detect_sections()` method in `resume_parser.py` uses regex patterns that
anchor section headers (like "Education" or "Skills") strictly to the start of
a line using `^` and `\n`. PDF-extracted text frequently preserves leading
indentation/whitespace before section headers, so these anchors never match
and `detected_sections` returns an empty list even when sections clearly
exist. This breaks downstream logic in the ingestion pipeline that depends on
knowing which resume sections are present. A successful fix will make the
regex patterns tolerant of leading whitespace so indented section headers are
correctly detected.

**Branch name:** fix/147-resume-section-detection-leading-whitespace

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**

Paraphrase the issue without looking at it. If you can't, you don't understand it well enough yet. Read the full issue body, look at any linked PRs or comments, and try again.

[X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.

**Do I understand which part of the app is affected?**

Check the labels on the issue — they often indicate the area (api, rag, ingestion, frontend, etc.). Look at the referenced files if any are mentioned. Find those files in the repo.

[X] I've located the relevant files and confirmed they exist in the codebase.

**Do I understand what "done" looks like?**

Can you describe what the app should do (or not do) once the issue is fixed? If the issue has acceptance criteria, read them carefully. If it doesn't, try writing your own — that forces you to understand the scope.

[X] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

---

### Part 2 — Tier Fit

**Is the tier a realistic match for where I am right now?**

[X] If this is my first open source contribution: I'm choosing Tier 1.

[ ] If I've contributed to large codebases before: Tier 2 or 3 is fair game.

[ ] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

---

### Part 3 — Codebase Readiness

**Can I find the relevant code?**

Before claiming the issue, locate the specific function, route, or module it describes. Don't rely on grep alone — open the file, read the surrounding context, and confirm you're in the right place.

[X] I've found and read the specific code the issue references (not just the file — the function or section).

**Do I understand the surrounding code well enough to change it safely?**

You don't need to understand the whole codebase. But you need to understand the file you're about to edit well enough to predict what a change will break. Read the function signatures, docstrings, and any callers.

[X] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.

**Have I read the relevant test file?**

Find the test file for the module your issue touches (tests/unit/ is the right place to start). Look at how existing tests are structured — fixtures, assertions, mock patterns. You'll need to write at least one new test.

[X] I've found the test file for my module and read at least one test end-to-end.

---

### Part 4 — Scope and Time

**How many others are already working on this issue?**

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

**Is the scope realistic for Weeks 8–9?**

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.

**Are there any blockers or dependencies?**

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[X] This issue has no open blockers or dependencies on other unresolved issues.

---

## Week 8 — Reproduction & solution planning

### Reproducing the Bug

**Command used:**
```
cd pathreview
python -m pytest tests/unit/test_resume_parser.py -k "no_work_experience or detect_sections" -v
```

**Result:** 2 failed, 8 deselected

```
FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_parse_resume_no_work_experience
  assert False
   +  where False = any(<generator ...>)
  # detected_lower has no "education" entry

FAILED tests/unit/test_resume_parser.py::TestResumeParser::test_detect_sections
  assert 0 > 0
   +  where 0 = len([])
  # _detect_sections() returned [] entirely
```

**Why this reproduces it without writing new test code:**
Both existing tests build their sample resume text as indented Python
triple-quoted strings (e.g. `resume_no_work = """\n        Education:\n ..."""`),
which is a natural way to write multi-line text inline in a test function.
Because the string is indented to match the surrounding code, every line
carries leading whitespace before words like `Education:` and `Skills:`.

`_detect_sections()`'s regex patterns anchor with bare `^`/`\n` immediately
followed by the section word (e.g. `^education\s*[:|-]`), with no `\s*`
allowance *before* the word. Leading indentation breaks that anchor, so the
section is never matched — `detected_sections` comes back empty even though
"Education" and "Skills" are clearly present in the text.

**Minimal interactive repro:**
```python
from ingestion.parsers.resume_parser import ResumeParser

parser = ResumeParser()
text = "        Education:\n        BS Computer Science"
parser._detect_sections(text)
# Actual:   []
# Expected: ["Education"]
```

**Root cause location:** `_detect_sections()` patterns at
[resume_parser.py:134-139](pathreview/ingestion/parsers/resume_parser.py#L134-L139) —
`\s*` appears only after the section word (trailing whitespace / before the
`:`/`|`/`-` separator), never before it, so indented headers are silently
missed.

**Reproduction commit link:** https://github.com/EmiEscu/pathreview/commit/588c30e

**PLAN.md link:** https://github.com/EmiEscu/pathreview/blob/fix/147-resume-section-detection-leading-whitespace/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Still deciding between `\s*` and `[ \t]*` for the whitespace allowance — need to confirm which avoids false-matching across newlines.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the regex fix in `_detect_sections()` (PLAN.md steps 1–2): added `[ \t]*` leading-whitespace tolerance and removed redundant `\n`-anchored patterns. Confirmed the 3 tests named in issue #147 (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) now pass. Added a new test, `test_detect_sections_with_tab_indentation`, covering the tab-indentation edge case from PLAN.md.

**Next steps:**
Run full `make check` / `make test-unit`, open a draft PR for peer review, and address any feedback before marking it ready.

**Blockers:**
None. Confirmed two pre-existing test failures (`test_parse_markdown_resume`, `test_strip_markdown_syntax`) are unrelated to this issue — they stem from a separate bug in `_strip_markdown()`, out of scope for #147.
---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/530

**Branch:** fix/147-resume-section-detection-leading-whitespace

**What you built:**
Fixed `_detect_sections()` in `resume_parser.py` so section-header regex patterns tolerate leading whitespace, resolving the issue where PDF-extracted resumes with indented text returned an empty `detected_sections` list.

**Tests added or updated:**
Updated `tests/unit/test_resume_parser.py` — confirmed the three previously failing tests (`test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`, `test_detect_sections`) now pass, and added `test_detect_sections_with_tab_indentation` covering tab-indented headers as an additional edge case.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** Brian Brown (CodePath AI 201 2A Classmate)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

The environment setup took longer than I expected — installing the various dependencies, and especially getting Docker installed and running, ate up more time than actually understanding the bug itself. Once the codebase was up and running, the issue itself turned out to be fairly approachable. The second-hardest part was figuring out which failing tests actually mattered. `test_resume_parser.py` has a lot of unit tests covering parsing behavior broadly, so it took real reading and reasoning to isolate which ones were tied to my specific issue versus which ones were failing for unrelated, pre-existing reasons.

**What did you learn about working in a large codebase?**

The biggest lesson was how much good documentation and code organization matter once a project grows beyond something one person can hold in their head. Docstrings, a clear file structure, and a CONTRIBUTING.md that spells out conventions weren't just nice-to-haves — without them, I would have really struggled to even locate where the bug lived. My own personal projects rarely have a detailed `README.md` or contribution guide, since I'm usually the only one who needs to understand them. This module made it clear why that documentation becomes essential the moment more than one person touches the code.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for explaining unfamiliar functions and getting my local environment running — especially working through Docker, `winget`, and pre-commit hook issues that would have taken much longer to debug alone. Where they fell short was doing the actual detective work: pinpointing the precise root cause of the bug and designing a meaningfully new test case for the fixed behavior took my own close reading of the code, not AI suggestion.

**What would you do differently if you started over?**

I'd keep the same issue, but lean less on AI assistance during the actual implementation. I'd rather have taken a first pass at the fix myself and used AI to review and give feedback afterward, instead of leaning on it throughout. I'd also have used my `PLAN.md` more fully — I identified 5 edge cases and 3 risks during planning, but only ended up writing a test for one of them (tab indentation). Covering more of that ground would have made the fix more robust and the PR stronger.

**What are you most proud of from this module?**

I'm proud of how quickly I was able to trace the bug back to its exact location — it genuinely felt like solving a small mystery. I'm also proud of the  PR itself; I think the description and documentation turned out thorough and clear, laying out not just what changed but why.
