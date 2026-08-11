## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`extract_skills()` in `ingestion/parsers/skill_extractor.py` returns no detections at
all for text that clearly describes JavaScript work, and for TypeScript samples
(mentioning `.tsx`/`.ts` files and the word TypeScript) it detects only `React`.
Python, DevOps, and database detection all work correctly in the same file, so this is
isolated to the JS/TS-specific logic inside `_detect_languages()`. The fix is scoped to
a single file (`skill_extractor.py`) and its corresponding test file, with four
previously-failing tests named directly in the issue: `test_javascript_detection`,
`test_text_with_typescript_files`, `test_devops_tool_detection`, and
`test_docker_compose_detection`.

**Branch name:** fix/130-docker-memory-limits

**Setup confirmation:** [x] App runs locally

**Cohort ledger:** [x] Issue added to cohort ledger

**Note:** Previously claimed and documented issue #130 (Docker memory limits) for
Weeks 7-8, but investigation showed the bug did not reproduce against current main (no
LLM proxy service exists in `docker-compose.yml`, and existing services already had
memory limits configured). Switched to issue #148 for Week 9 submission since it
reproduces cleanly and is well-scoped to a single file. All #148 work is committed on
the same `fix/130-docker-memory-limits` branch rather than a fresh branch, since I
pivoted issues mid-stream rather than starting a new one — the branch name reflects the
original issue, not #148.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [paste the actual commit SHA/link here — run
`git log --oneline` on your branch and find the commit where you added the reproduction
notes or PLAN.md, then link it as
`https://github.com/GitNuckle/Pathreview/commit/4aa1e9a`]

**Reproduction notes:**
Ran the issue's two examples directly against `extract_skills()`:
```python
e.extract_skills('Wrote index.js using const arrow functions and async/await callbacks')
# -> [] (matches issue's reported observed output)

[d.name for d in e.extract_skills('Built app.tsx and types.ts with strict TypeScript interfaces')]
# -> ['React'] (matches issue's reported observed output)
```
Both matched the issue's "observed" output exactly, confirming the bug reproduces
cleanly on current main.

Read through `_detect_languages()` line by line to find the actual root cause:
- JS/TS detection is almost entirely gated on a `filename` argument, which is `None`
  in both repro calls.
- The only text-based JS check, `re.search(r"\b(import|require)\s+", text)`, requires
  whitespace after the keyword and neither example uses `import`/`require` at all —
  they use `const`, arrow syntax, and `async`/`await`, none of which are checked
  anywhere in the method.
- `JS_TS_KEYWORDS` is defined as a class attribute but never referenced in the method
  body — dead code, and the actual root cause.
- TypeScript is only ever assigned via `.ts` in `filename`; there's no content-based
  TS signal at all.
- React "detects" on the second example only because `.tsx` is a literal string in
  `REACT_INDICATORS` and happens to appear directly in the input text.

**PLAN.md link:** https://github.com/GitNuckle/Pathreview/blob/fix/130-docker-memory-limits/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:** None — issue reproduces cleanly and root cause is clear
from reading the code directly.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Investigated root cause in `_detect_languages()`; confirmed `JS_TS_KEYWORDS` was unused
dead code and TypeScript detection depended solely on `filename`.

**Next steps:**
Implement JS/TS regex-based evidence checks and add tests.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/980

**Branch:** fix/130-docker-memory-limits

**What you built:**
Rewrote JavaScript/TypeScript detection in `_detect_languages()` to check real syntax
(import/require, export, arrow functions, async/await, TS interfaces/type annotations)
instead of relying only on `filename`, so both languages can now be detected
independently from plain-text descriptions or real code with no filename provided.

**Tests added or updated:**
Added 4 tests to `tests/unit/test_skill_extractor.py`: `test_issue_148_javascript_description`
and `test_issue_148_typescript_description` (the issue's exact repro cases),
`test_plain_english_not_flagged_as_code` (guards against false positives on ordinary
English containing words like "class"/"let"), and
`test_tsx_file_detects_react_and_typescript` (confirms a real `.tsx` file produces both
React and TypeScript detections, not just one).

**Self-review confirmation:** [x] make test-unit equivalent (`pytest tests/unit/test_skill_extractor.py`)
run — all 4 new issue #148 tests pass, along with 15 of 18 pre-existing tests in the
file. 3 pre-existing tests fail (`test_database_technology_detection`,
`test_devops_tool_detection`, `test_docker_compose_detection`); the latter two are named
in the issue as related but are DevOps/Docker-detection gaps outside the JS/TS scope of
this fix — documented here rather than fixed to keep this PR scoped to #148.
[ ] `make check` — `make` is not available in my Windows environment; ran the touched
file through `pytest` directly instead as the closest equivalent available to me.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback has come in on the PR as of this entry.

**How you responded:**
[Leave blank — no feedback to respond to]

---

### Reflection

**What was harder than you expected?**
Getting the actual code changes to show up in the submitted PR was much harder than
writing the fix itself. I initially worked through the fix, tests, and documentation
correctly in isolation, but lost track of which branch I was actually on and whether
files were committed versus just saved locally. My Week 9 submission scored 3/20
because the grader found a completely different (unrelated) `skill_extractor.py` file
in the diff, not the one I'd actually fixed — the real fix existed on disk but hadn't
been committed/pushed correctly. Running `git status` and `git diff main --stat` before
submitting would have caught this in seconds, and I didn't think to do it under time
pressure. I also broke my test file at one point by pasting only the new test methods
and overwriting the entire original file, deleting the imports, fixture, and 18 existing
tests in the process — that took a full re-read of the original file to recover from.

**What did you learn about working in a large codebase?**
The most useful thing was learning to verify assumptions against the actual code instead
of trusting a bug report's description. The issue said TypeScript detection was broken,
but reading `_detect_languages()` line by line showed the real root cause was more
specific: a class attribute (`JS_TS_KEYWORDS`) was defined but never referenced anywhere,
and TypeScript detection depended entirely on a `filename` argument that's often `None`.
I also learned that this same codebase has two entirely separate `SkillExtractor`
classes in different modules (`agent/tools/skill_extractor.py` and
`ingestion/parsers/skill_extractor.py`) — in a large, real codebase, similarly-named
files are a real risk, and confirming the exact file path matters as much as
understanding the logic inside it.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for reading through the existing detection logic quickly,
identifying the exact regex causing the bug, and drafting the new evidence-check
patterns and tests in a style that matched the existing code. Where it fell short was
in verifying that changes actually landed correctly in my real environment — the AI
could sanity-check logic in an isolated sandbox, but couldn't see my actual git state,
which branch I was on, or that I'd pasted an incomplete replacement into a file. That
verification step had to be done by me, running `git status`, `git diff`, and `pytest`
directly and reporting the real output back.

**What would you do differently if you started over?**
I'd run `git branch` and `git status` before making any changes, to confirm I was on a
fresh branch actually named for the issue I was solving (I ended up committing #148
work onto a leftover `fix/130-docker-memory-limits` branch from an earlier issue I'd
abandoned). I'd also run `pytest` immediately after adding new tests, before considering
any work "done," rather than assuming a file replacement worked without checking test
collection output.

**What are you most proud of from this module?**
Tracing the root cause precisely — identifying that `JS_TS_KEYWORDS` was dead code and
that JavaScript/TypeScript detection needed to be independent (not mutually exclusive)
labels so a `.tsx` file could correctly register as both. That distinction wasn't
explicitly stated in the issue; I found it by testing a realistic `.tsx` file case and
confirming the fix needed to produce two detections at once, not just fix one broken
label.