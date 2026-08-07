## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now the ingestion pipeline only infers skills from import statements and README text, so contributors who set up and maintain CI/CD pipelines get no credit for that work — their DevOps experience is invisible to the skill extractor. This issue asks for a new parser that reads `.github/workflows/*.yml` files in a repo and infers skills like GitHub Actions, Docker, pytest, and deployment from the workflow configuration (jobs, steps, actions used, etc.). The fix touches the ingestion pipeline: a new `ingestion/parsers/workflow_parser.py` module plus changes to `ingestion/parsers/skill_extractor.py` to wire the new parser's output into the overall skill extraction results. Estimated effort is 6–10 hours, and it's labeled tier-3 since it involves adding a new architectural piece to the ingestion/skill-detection system rather than a small isolated fix.

**Branch name:** feat/14-github-action-parser-for-skills

**Setup confirmation:** [x] (https://github.com/ascherj/pathreview/issues/14) App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/somabadri/pathreview/commit/88d643cb55fc0bbcd14698cc04e13e33d2635e00

**Reproduction summary:**
This is a new feature rather than a bug, so there's no failing behavior to reproduce — instead I confirmed the gap by tracing the ingestion pipeline and confirming no code path reads `.github/workflows/*.yml`. The commit above locates the placeholder `ingestion/parsers/workflow_parser.py` where the new parser will be added.

**PLAN.md link:** https://github.com/somabadri/pathreview/blob/feat/14-github-action-parser-for-skills/PLAN.md

**Walkthrough video (recommended):** N/A — no walkthrough video since this is a new feature with no existing behavior to demo.

**Blockers or open questions:**
How to structure the implicit skill mappings for workflow-derived skills (actions used, run commands → GitHub Actions/Docker/pytest/deployment). Still deciding between hardcoding a keyword map similar to `skill_extractor.py`'s existing `FRAMEWORKS`/`TOOLS` dicts, or a different approach.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all of PLAN.md's sub-tasks: added the `PyYAML` dependency, built `WorkflowParser.parse()` (triggers, job names, `uses:` actions, `run:` commands, including the PyYAML `on:` → `True` boolean gotcha and `ValueError` handling for malformed/non-mapping YAML), extended `SkillExtractor` with a `_detect_ci_cd` step + `CI_CD_INDICATORS` map (GitHub Actions, Pytest, Deployment — Docker is left to the existing `TOOLS` detection), and wired `ingest_workflow(...)` into `IngestionPipeline`, one call per workflow file.

**Next steps:**
Finish `make check`/`make test-unit` self-review against the pre-existing baseline, open the draft PR for peer/mentor feedback, and address anything that comes back before marking it ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/948

**Branch:** `feat/14-github-action-parser-for-skills`

**What you built:**
A `WorkflowParser` that reads `.github/workflows/*.yml` content into text + metadata (triggers, job names, actions used, run commands), and a `SkillExtractor._detect_ci_cd` step that turns that output into CI/CD skill detections (GitHub Actions, Pytest, Deployment), all wired into `IngestionPipeline.ingest_workflow(...)`.

**Tests added or updated:**
`tests/unit/test_workflow_parser.py` (new, 16 tests covering standard/single-job/list-trigger workflows, malformed YAML, missing `jobs`/`steps`, bytes input, and metadata structure) and `tests/unit/test_skill_extractor.py` (5 new tests for GitHub Actions/Pytest/Deployment detection, CI/CD category tagging, and no false positives on unrelated text). Confirmed via `git stash` diffing that pre-existing ruff/mypy/test failures (183 ruff, 103 mypy, 53 test failures at baseline) are unchanged by these additions.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none yet


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review or comments have come in on PR #948 as of this check-in. Per the Su26 course note, reviewer feedback isn't a standard feature this term, so this is expected rather than a signal about the PR itself.

**How you responded:**
N/A — no feedback to respond to. Left the PR open and ready for review; no further changes made this week beyond re-verifying `make check`/`make test-unit` still pass against the current baseline.

---

### Reflection

**What was harder than you expected?**
Designing the skill-mapping approach for `CI_CD_INDICATORS` took longer than expected. The blocker I flagged back in Week 8 — hardcoded keyword map (matching the existing `FRAMEWORKS`/`TOOLS` pattern in `skill_extractor.py`) vs. something more structured — didn't have an obviously correct answer, and going back and forth on it ate more time than the actual parsing logic did. In hindsight the existing codebase already had a strong convention (the keyword-map dicts), and I should have trusted that convention sooner instead of treating it as an open design question.

**What did you learn about working in a large codebase?**
The real cost wasn't writing new code, it was proving the new code didn't break anything that was already broken. `pathreview` has a pre-existing baseline of failures (183 ruff, 103 mypy, 53 test failures) that have nothing to do with my change, and I had to `git stash` my diff and re-run the checks to confirm those numbers were unchanged before I could trust my own results. In a solo project there's no such thing as a "pre-existing failure" to control for — everything failing is yours. Contributing to someone else's production code means the bar isn't "my code works," it's "my code doesn't move any number that isn't already mine to move."

**How did AI tools help — and where did they fall short?**
AI was most useful for drafting the mechanical parts fast — the YAML parsing scaffolding, the initial pass at `WorkflowParser.parse()`, and generating the bulk of the 21 unit tests once I'd decided what needed covering. Where it fell short was exactly the baseline-verification step above: an assistant can't tell you which of 53 failing tests are pre-existing versus newly introduced by your change — that required me to actually stash my diff, re-run the suite against a clean tree, and diff the two failure counts myself. It's a check that only works if you distrust your own change enough to isolate it, which isn't something you can delegate.

**What would you do differently if you started over?**
Not much — issue selection, planning, and the build itself went the way I expected them to, given the PLAN.md I wrote in Week 8. If anything, I'd resolve the skill-mapping design question faster by defaulting to the codebase's existing convention instead of treating it as open-ended, per the note above.

**What are you most proud of from this module?**
Catching the PyYAML `on:` gotcha — where PyYAML silently parses the bare YAML key `on:` as the boolean `True` rather than the string `"on"` — before it caused a subtly wrong trigger detection in `WorkflowParser`. It's the kind of bug that wouldn't show up in a quick manual test, only in test cases that specifically exercise real GitHub Actions workflow files, and catching it during implementation rather than after review felt like the moment I was actually thinking like a maintainer of this codebase rather than just a contributor bolting on a feature.