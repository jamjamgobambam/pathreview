## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
tech_detector.py fails to filter out biuld-output files such as node_modules/ and build/ directories. This causes the vendored or bundles files to be counted alongside actual source code. As a result, it is misclassified as primarily JavaScript instead of Python. There is failed tests.

**Branch name:** fix/150-tech-detector-skewing-language-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/fuentesjm/pathreview/commit/65e11fd9b7987b1465447a556e5d8f89093c206c



**Reproduction summary:**
I ran pytest tests/unit/test_tech_detector.py and found test_node_modules_excluded and test_build_directory_excluded already failing: a repo with a root-level node_modules/ or build/ directory reports primary_language: "JavaScript" instead of "Python". The root cause is _should_skip_file, whose skip patterns require a leading slash (/node_modules/), so top-level vendored/build directories are never excluded and their files skew language detection.

**PLAN.md link:** https://github.com/fuentesjm/pathreview/blob/fix/150-tech-detector-skewing-language-detection/PLAN.md


**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All four PLAN.md sub-tasks are complete. The root cause — `_should_skip_file` matching pre-slashed patterns (`/node_modules/`) so top-level vendor/build directories were never excluded — is fixed by matching whole path segments against a centralized `SKIP_DIRS` set, with backslash normalization for Windows paths (commit `05961b8`). The two originally-failing tests (`test_node_modules_excluded`, `test_build_directory_excluded`) now pass, and I added 6 regression tests covering root-level `node_modules/`/`dist/`/`vendor/`/`.venv/`, a guard that filenames merely containing a keyword (`rebuild.py`) are not skipped, and a fully-vendored repo → `Unknown` (commit `2cc33dd`). The `tech_detector` suite is 33/33 green.

**Next steps:**
Open the PR against `ascherj/pathreview` using the PR template, documenting the pre-existing repo failures and stating my change introduces none. Optionally record a short walkthrough video. Then complete the Check-in 2 self-review boxes.

**Blockers:**
None. 

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/366

**Branch:** `fix/150-tech-detector-skewing-language-detection`

**What you built:**
Fixed the tech detector so vendored and build-output files are no longer counted as project source. `_should_skip_file` now splits each path into segments and matches them against a `SKIP_DIRS` set (with backslash normalization), so top-level directories like `node_modules/`, `build/`, and `dist/` are excluded — not just nested ones — which stops a Python project from being misreported as primarily JavaScript.

**Tests added or updated:**
`tests/unit/test_tech_detector.py` — added 6 regression tests: root-level `node_modules/`, `dist/`, `vendor/`, and `.venv/` exclusion; a guard that filenames merely containing a skip keyword (`rebuild.py`, `vendored_data.py`) are not excluded; and a fully-vendored repo resolving to `Unknown`. The two previously-failing tests (`test_node_modules_excluded`, `test_build_directory_excluded`) now pass — the suite is 33/33 green.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both exit non-zero only due to pre-existing failures unrelated to #150 — identical on base commit `fb93406` (181 ruff / 103 mypy / 51 unit). My change introduces no new failures and fixes 2 unit tests; changed files are ruff + mypy clean.)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [x] No — still awaiting review

**Summary of feedback:**
No Feedback.

**How you responded:**
No Feedback.

---

### Reflection

**What was harder than you expected?**
Getting the app running was as hard as attempting to fix the issue. A Postgres port 5433 collided with the Docker container port I had on my laptop which made the setup say "password athentication failed". It took longer than expected to fix that issue before I can fix issue 150.

**What did you learn about working in a large codebase?**
Working on a large codebase can throw me off. I tend to find out you need to isolate your issue that you need to tackle and avoid going to a rabbit hole realizing the repo had uunrelated unit-test failures caused by other issues.

**How did AI tools help — and where did they fall short?**
Helping me understand the code more clearly. Reassuring that what I understand about the repo is true. It was also useful in helping me locate the bug and find out the real root of the problem. Where it fall short is sometimes it will get carried away so you have to know that AI is just focusing on one particular issue not many,

**What would you do differently if you started over?**
Planning I will do differently. I will next time make sure to reproduce the bug many times and not go straight into fixing it. Keeping the branch cleaner will be on I will do differently next time.

**What are you most proud of from this module?**
I am most proud of being able to write git command lines in terminal. Figuring out and constributing the a large repo. Being able to understand how to use AI efficiently.