## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/FahmidaAz/pathreview/commit/4fe7555

**Reproduction summary:**
Ran the existing test suite for `tests/unit/test_skill_extractor.py` and
confirmed 4 tests fail exactly as the issue describes. Also manually
reproduced via the Python shell using the exact repro snippet from the
issue — `extract_skills()` returned `[]` for JavaScript text and `['React']`
(no TypeScript) for TypeScript text.

**PLAN.md link:** https://github.com/FahmidaAz/pathreview/blob/fix/148-skill-extractor-js-ts-detection/PLAN.md

**Walkthrough video (recommended):** (leave blank if you don't record one)

**Blockers or open questions:**
Need to decide exactly how many distinct JS/TS keyword matches should be
required before flagging a language, to avoid false positives on
Python-only text that happens to use `class`/`async`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full fix in `ingestion/parsers/skill_extractor.py` per PLAN.md:
JS/TS keyword-based detection using the previously-unused JS_TS_KEYWORDS set,
TypeScript-specific syntax indicators for correct labeling, and Dockerfile/
docker-compose syntax detection in `_detect_tools()`. All 4 target tests
(`test_javascript_detection`, `test_text_with_typescript_files`,
`test_devops_tool_detection`, `test_docker_compose_detection`) now pass.

**Next steps:**
Run `make check` and `make test-unit` for a final confirmation, write the PR
description, and open the pull request against `ascherj/pathreview`.

**Blockers:**
None. Note: `make check` surfaced ~180 pre-existing lint errors and
`make test-unit` surfaced 49 pre-existing test failures across unrelated
files (other students' curated issues) — confirmed my changed file
(`skill_extractor.py`) is clean on all three checks (ruff/black/mypy) and
introduces no new test failures.
### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/487

**Branch:** fix/148-skill-extractor-js-ts-detection

**What you built:**
Fixed `extract_skills()` in `ingestion/parsers/skill_extractor.py` to detect JavaScript/TypeScript from keyword and syntax patterns (not just filenames/imports), and to detect Docker/docker-compose usage from Dockerfile/YAML syntax even when the literal word "docker" never appears.

**Tests added or updated:**
No new tests added — the 4 existing tests named in issue #148 (`test_javascript_detection`, `test_text_with_typescript_files`, `test_devops_tool_detection`, `test_docker_compose_detection`) already defined the target behavior and now all pass.

**Self-review confirmation:** [x] make check passes (clean on changed file; confirmed via ruff/black/mypy)  [x] make test-unit passes (no new failures; 49 pre-existing failures unrelated to this change, documented in PR)

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback yet as of submission. Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a gap on my end.

**How you responded:**
N/A — no feedback received. I did share my draft PR link in the cohort ledger for visibility/peer review before marking it ready.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running took far longer than fixing the actual bug. I hit a chain of unrelated problems before I could even run a test: Docker Desktop needing WSL2, a ChromaDB Docker image that broke on startup because it silently pulled NumPy 2.0 (removing `np.float_`, which the pinned chromadb version still relied on), a literal syntax typo in the Makefile (`&;`) that broke `make run` on any OS, and a corrupted `.bashrc` from accidentally running a bash command in PowerShell first. None of that was related to my issue — it was just the cost of getting a real, unfamiliar, multi-service codebase running on my machine. The actual code fix was maybe 40 lines.

**What did you learn about working in a large codebase?**
The most useful discovery wasn't in my issue's description — it was noticing that `skill_extractor.py` already had a `JS_TS_KEYWORDS` set defined but never used anywhere. That told me someone had planned to use keyword matching and never finished wiring it in, which shaped my whole fix. I also learned to check whether an issue already has an open PR before claiming it — I initially claimed issue #155, only to find another contributor had already opened a PR fixing it (and several other "easy" issues) within hours. Large, actively-worked codebases move fast, and claiming something doesn't mean it's still available by the time you sit down to work on it.

**How did AI tools help — and where did they fall short?**
AI was most useful for tracing root causes across a file I'd never seen before — reading `_detect_languages()` line by line to figure out exactly why `require('fs')` didn't match a regex, rather than guessing. It also helped a lot with process: drafting `PLAN.md` and my PR description in the exact formats required, and systematically working through Docker/Makefile errors one at a time instead of guessing randomly. Where it fell short: it couldn't directly browse the live GitHub issue tracker or run commands on my machine, so a lot of steps required me to run things myself and share screenshots back and forth — slower, but it meant I actually understood every step rather than having it done for me.

**What would you do differently if you started over?**
I'd check for existing PRs against an issue before claiming it, not after. I'd also get my terminal environment (Git Bash specifically, not PowerShell or CMD) sorted out on day one instead of bouncing between three different shells, which caused most of my early confusion (like the `.bashrc` encoding corruption). And I'd skim the whole `Makefile` early on, rather than discovering its bugs one at a time only when a command failed.

**What are you most proud of from this module?**
Getting a genuinely broken Windows dev environment (Docker, WSL2, a broken vendored Docker image, a broken Makefile) fully working end-to-end without giving up on any single blocker, and then writing a fix that stayed tightly scoped — I found several unrelated pre-existing bugs along the way (a test file typo, ~180 lint errors, a broken `make typecheck` target) and documented them instead of trying to fix everything at once.