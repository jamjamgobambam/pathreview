# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [x] Tier 2

**Problem summary:**
Right now the ingestion pipeline only pulls a candidate's profile data from their resume upload and their GitHub repos (READMEs and repo metadata) — there's no way to bring in content from a personal portfolio site, even though the `Profile` model already has a `portfolio_url` field sitting unused. This means bio text and project write-ups that only live on someone's portfolio page never make it into the vector store, so the review agent can't reference them when generating feedback. A successful fix adds a way to fetch that URL's HTML, strip out navigation/boilerplate, pull out the meaningful text (About/bio and project descriptions), and run it through the same chunk-and-embed flow the other sources use, storing it alongside the resume and GitHub content. It touches the ingestion layer (a new `web_parser.py` parser and a new method on `ingestion/pipeline.py`) and the profile API schema.

**Branch name:** 11-portfolio-url-ingestion

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Selection notes ("is this right for me?" checklist reasoning)

- **Scope fits a Tier 2 issue:** touches one new parser file plus small, well-scoped additions to the existing pipeline and schema — not a cross-cutting refactor.
- **Clear acceptance criteria:** the issue names the exact files to touch (`ingestion/parsers/`, `ingestion/pipeline.py`, `api/schemas/profile.py`), which matches the estimated 5–8 hour effort.
- **Follows an existing pattern:** `ResumeParser`/`ReadmeParser` + `IngestionPipeline.ingest_resume`/`ingest_readme` are direct templates to mirror, so the unknowns are mostly in the new part (fetching an arbitrary user-supplied URL safely) rather than in the whole pipeline shape.
- **New risk worth flagging early:** unlike the other sources, this one fetches a URL the user supplies, so SSRF protection (blocking internal/private addresses, restricting redirects) needs to be part of the implementation, not an afterthought.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/NadaFeteiha/pathreview/commit/7f7b868

**Reproduction summary:**
Since this issue describes a missing feature rather than a crash, I reproduced it by inspecting `main` along both paths a portfolio URL could take. I confirmed `ingestion/pipeline.py` has no `ingest_portfolio` method and `ingestion/parsers/` has no web/HTML parser, and that `api/routes/profiles.py` stores `portfolio_url` but never reads it back to fetch anything. I also found that `core/services/review_service.py::_run_ingestion_pipeline` references `profile.portfolio_url`, but only inside an explicit `# Placeholder: actual portfolio ingestion logic` block that fabricates a string instead of fetching real content. Full trail in `docs/issue-11-repro.md`.

**PLAN.md link:** https://github.com/NadaFeteiha/pathreview/blob/11-portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
`core/services/review_service.py` has a review-generation-time placeholder for portfolio (and github/resume) data that this fix does not touch — see the Risks section in PLAN.md. Worth confirming with a mentor whether that's tracked as a separate issue or expected to be addressed later, since without it the ingested portfolio content isn't yet surfaced end-to-end in a generated review.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are implemented: `WebParser` with SSRF-guarded `fetch_url` (including manual redirect re-validation), `IngestionPipeline.ingest_portfolio()` with metadata sanitization and stale-chunk cleanup, `portfolio_url` schema validation, the `BackgroundTasks` wiring in `api/routes/profiles.py` backed by a cached pipeline factory in `api/dependencies/ingestion.py`, and 31 unit tests across `test_web_parser.py` and `test_ingestion_pipeline.py`, all passing.

**Next steps:**
Run `make check`/`make test-unit` against `main` to establish a pre-existing-failure baseline, self-review the diff against `CONTRIBUTING.md` and the pre-submission checklist, rewrite the PR description to the repo's template, and finalize.

**Blockers:**
None blocking; the review_service.py placeholder noted in Week 8 remains an open question for a mentor, not a blocker for this PR's scope.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/168

**Branch:** `11-portfolio-url-ingestion` (see Notes for Reviewers on the PR for why this doesn't carry the `feat/` prefix required by `CONTRIBUTING.md` — GitHub doesn't support retargeting an open PR to a renamed branch, so the rename was reverted to avoid closing/reopening the PR)

**What you built:**
A `WebParser` that fetches a portfolio URL (with an SSRF guard covering redirects) and extracts clean bio/project text, plus an `IngestionPipeline.ingest_portfolio()` method that chunks, embeds, and stores that text in the vector store — triggered automatically in the background when a profile is created or updated with a `portfolio_url`.

**Tests added or updated:**
`tests/unit/test_web_parser.py` (20 tests: parsing, boilerplate stripping, metadata, SSRF guard, redirect handling) and `tests/unit/test_ingestion_pipeline.py` (11 tests: metadata sanitization, stale-chunk cleanup, ingest success/failure paths) — 31 total, all passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both checked under the documented pre-existing-failure carve-out: `main` already has 53 failing unit tests and repo-wide ruff/black/mypy failures unrelated to this change. On the 9 files this PR touches, ruff/black/mypy introduce 0 new errors — full breakdown in the PR's Notes for Reviewers.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviews or comments have landed on PR #168 as of this entry (confirmed via `gh pr view 168 --json reviews,comments` — both empty). I shared it in the cohort Slack channel; nothing back yet.

**How you responded:**
N/A — nothing to respond to yet. If feedback comes in after this entry, I'll add a follow-up note rather than edit this section, so the record of what happened when stays honest.

---

### Reflection

**What was harder than you expected?**
Getting the ingestion logic itself right was the easy part — `ResumeParser`/`ReadmeParser` and `ingest_resume`/`ingest_readme` were direct templates, so the new parser and pipeline method almost wrote themselves. What actually took real effort was everything *around* the happy path. I shipped a first version of `fetch_url` with an SSRF guard that checked the URL's host before fetching — but I'd left `httpx`'s `follow_redirects=True` on, which meant a public URL could 302 straight into `169.254.169.254` and the guard would never see it. That only surfaced because I asked for a dedicated senior-engineer review pass after the "working" version was already committed. If I'd shipped that first version, I would have merged a security control that looked correct in every test I'd written but didn't actually hold under the one attack it existed to stop. The same review pass caught a second, non-security bug: I was writing `extracted_sections` (a list) and `title` (nullable) straight into chunk metadata, and ChromaDB only accepts scalar values — so the feature would have silently failed on every real ingestion despite all 20 of my original tests passing, because none of those tests exercised the actual vector-store write path.

**What did you learn about working in a large codebase?**
The most useful skill wasn't writing new code, it was reading old code carefully before touching anything. Confirming issue #11's scope meant diffing against `main` and grepping the *whole* codebase for `portfolio_url`, not just the three files the issue listed — that's how I found `core/services/review_service.py::_run_ingestion_pipeline`, a completely separate, review-generation-time code path that also references `portfolio_url` but only inside a hardcoded placeholder. It would have been easy to either miss it entirely or, worse, assume it was in scope and start "fixing" it, expanding a 5–8 hour issue into something much bigger. I also learned to distrust my own local `make check`/`make test-unit` runs until I'd established a baseline on `main` first — this repo has 53 pre-existing failing unit tests and 168 pre-existing ruff errors that have nothing to do with issue #11, and without checking `main` first I could easily have either panicked over failures I didn't cause or, worse, missed a real regression buried in the noise.

**How did AI tools help — and where did they fall short?**
AI was fastest at the mechanical parts: finding the exact sibling pattern to mirror (`ResumeParser`, `ingest_resume`), scaffolding a new parser and pipeline method consistently with house style, running `pytest`/`ruff`/`black` in a tight loop, and diffing against `main` to separate what I broke from what was already broken. Where it fell short was catching subtle correctness and security issues on the first pass — the redirect-based SSRF bypass and the ChromaDB list/`None` metadata bug both survived an initial "it works and the tests pass" implementation and only surfaced when I explicitly asked for an adversarial review rather than a "does this look done" pass. The lesson isn't "don't use AI for security-sensitive code," it's that a first implementation pass and a critical review pass are different modes and need to be asked for separately — treating the first green test run as the finish line would have shipped both bugs.

**What would you do differently if you started over?**
Two concrete things. First, I'd nail down the branch naming convention before opening the PR, not after — I renamed the branch mid-stream to match `CONTRIBUTING.md`, discovered GitHub can't retarget an open PR's head branch, and had to unwind the rename to avoid closing and reopening PR #168, which cost time and left a documented (but avoidable) deviation in the final PR. Second, I'd run the adversarial/security review pass as its own explicit step right after the first working version, instead of treating "tests pass" as a stopping point and only requesting a deeper review afterward — both real bugs I found came from that second pass, and they should be a standard step in my process, not something I ask for occasionally.

**What are you most proud of from this module?**
Not the feature working — catching the SSRF redirect bypass before it shipped. It's the kind of bug that passes every functional test, looks like exactly the right defense in the diff, and would only ever be found by someone deliberately trying to break it rather than confirm it works. Building the habit of asking "how would this fail against someone trying to abuse it" as a separate step from "does this do what I intended" feels like the most transferable thing I'm taking out of this module.
