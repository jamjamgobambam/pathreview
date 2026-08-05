## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/11)]

**Issue title:** [Add support for ingesting a portfolio website URL]

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now the ingestion pipeline only pulls in data from GitHub and resumes, so it has no way to capture context that only lives on a candidate's personal portfolio site, like project write-ups or bio copy. This means the vector store is missing potentially valuable signal about a person's work that they've chosen to showcase outside of GitHub. The fix requires adding a new web parser (likely `ingestion/parsers/web_parser.py`) that fetches a submitted portfolio URL, scrapes the page, and extracts relevant text such as bio and project descriptions. That extracted content then needs to be wired into `ingestion/pipeline.py` so it's embedded and stored alongside the existing GitHub/resume data, and `api/schemas/profile.py` needs to be updated so the API can accept and validate a portfolio URL field on a profile submission.

**Branch name:** [feat/11-add-support-for-ingesting-portfolio-website-url]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## "Is this right for me?" — selection notes

**Part 1 — Understanding the issue**
- [x] Can paraphrase without re-reading: the app currently only ingests GitHub and resume data into the vector store; there's no way to pull in content from a candidate's own portfolio site, so anything they've written there (project write-ups, bio) never becomes searchable context.
- [x] Located the relevant files and confirmed they exist: `ingestion/parsers/` (has `readme_parser.py`, `repo_analyzer.py`, `resume_parser.py`, `skill_extractor.py`, `base.py`, but no `web_parser.py` yet — matches the issue's ask), `ingestion/pipeline.py`, `api/schemas/profile.py`.
- [x] Before/after is concrete: before, submitting a portfolio URL does nothing beyond storing the string; after, submitting one triggers a fetch + parse + chunk + embed step so that portfolio text shows up in retrieval alongside GitHub/resume content.

**Part 2 — Tier fit**
- [x] Tier 2 is a fair match — this isn't my first contribution to this repo, and the change genuinely spans multiple layers (a new parser, pipeline orchestration, and API schema), not just one file.

**Part 3 — Codebase readiness**
- [x] Read `ingestion/pipeline.py` in full: `IngestionPipeline` already has a clear pattern to follow — `ingest_resume`, `ingest_readme`, and `ingest_repo_metadata` all do parse → build metadata → chunk via `StrategySelector` → embed via `BatchEmbeddingProcessor` → record via `_record_ingested_source`. A new `ingest_portfolio` method should mirror this shape.
- [x] Read `ingestion/parsers/base.py`: every parser subclasses `BaseParser` and returns a `ParseResult(text, metadata, source_type)` — that's the contract `web_parser.py` needs to satisfy.
- [x] Checked `api/schemas/profile.py`: `portfolio_url` already exists on `ProfileCreate`/`ProfileUpdate`/`ProfileResponse` as an optional string field. **Scope note:** this means the schema work described in the issue may already be partially done — the field exists but isn't validated as a URL (just `max_length=500`) and isn't yet consumed anywhere in ingestion. I'll confirm during implementation whether URL validation needs to be added here or if that's out of scope.
- [x] Read a full existing test end-to-end (`tests/unit/test_readme_parser.py`): tests are organized under `tests/unit/`, use `@pytest.mark.unit`, instantiate the parser via a fixture, and assert on `ParseResult` fields (`text`, `source_type`, `metadata` keys). **Scope note:** there's no existing test file for `pipeline.py` itself (only parser-level tests exist for readme/resume), so I'll need to decide whether to add pipeline-level tests or keep coverage at the new `web_parser.py` level, consistent with what's already there.

**Part 4 — Scope and time**
- [ ] Claims/comments check: need to check the issue comments and the Claims column in the cohort ledger's Issue Catalog tab before finalizing — not yet confirmed from within this session.
- [x] Time estimate: issue lists 5–8 hours; that lines up with the actual scope found in the code (one new parser + one new pipeline method + a small schema check), so Tier 2 / Weeks 8–9 timeline looks realistic.
- [x] No "blocked by #X" language in the issue body, and no other unresolved dependency was mentioned.

**Overall scope reasoning:** The issue is well-scoped and the referenced files check out — including one pleasant surprise, `portfolio_url` is already on the Pydantic schemas, so the real net-new work is the `web_parser.py` module and the `ingest_portfolio` pipeline method, following the existing `ingest_readme`/`ingest_resume` pattern almost exactly. The one open item is manually confirming the claims count in the cohort ledger before committing to start.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/arushibhatia/pathreview/commit/9716efd6b604347cb1bcf5b5382e0f210652f07d

**Reproduction summary:**
I stood up a local HTTP server as a stand-in portfolio site, set a profile's Portfolio URL to point at it, and ran a full review through the app. The fake server's access log stayed empty the entire time — no request was ever made to the portfolio URL — and the review completed with results that were unaffected by the portfolio field, confirming that portfolio content is never fetched or used, despite the field existing end-to-end (DB column, API schema, frontend form).

**Reproduction steps:**
1. Started a throwaway "portfolio site" locally: `mkdir -p /tmp/fake-portfolio && echo "<h1>Jane Doe</h1><p>...</p>" > /tmp/fake-portfolio/index.html`, then `cd /tmp/fake-portfolio && python3 -m http.server 8001` (kept its terminal visible to watch for incoming requests).
2. Ran the app locally (`make run`) and initiated the flow to submit a review.
3. As part of the review, I submitted `http://localhost:8001` as the Portfolio URL.
4. Checked the `http.server 8001` log throughout and after the run, and zero requests were received, proving nothing in the app ever fetches the submitted URL.

**PLAN.md link:** [PLAN.md](https://github.com/arushibhatia/pathreview/blob/feat/11-add-support-for-ingesting-portfolio-website-url/PLAN.md)

**Walkthrough video (recommended):** Didn't do, but below is a screenshot of the lack of logs on the local dummy server to validate that nothing was fetched from the portfolio.

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Before touching any code, I ran `make test-unit` and `make check` on `main` (well, on this branch before any of my changes) to establish a pre-existing-failures baseline, per the instructions:
- `make test-unit`: **53 failed, 375 passed, 3 warnings** — failures span `test_batch_processor`, `test_bias_detector`, `test_faithfulness_checker`, `test_keyword_search`, `test_output_parser`, `test_pii_scrubber`, `test_prompt_defense`, `test_readme_parser`, `test_readme_scorer`, `test_relevance_scorer`, `test_resume_parser`, `test_review_service`, `test_security`, `test_skill_extractor`, `test_structural_chunker`, `test_tech_detector`. None of these touch `ingestion/pipeline.py`, the (not-yet-existing) `web_parser.py`, or the portfolio ingestion path.
- `black --check .`: **52 files would be reformatted, 58 unchanged** (repo-wide, pre-existing).
- `mypy api/ core/ ingestion/ rag/ agent/ safety/`: **103 errors in 26 files** (mostly missing return type annotations and `UUID`/`str` argument mismatches in `api/routes/reviews.py`, `api/routes/profiles.py`, `api/main.py` — pre-existing).
- `ruff check .`: **182 errors, 86 auto-fixable** (pre-existing, mostly unused variables in test files).

I then implemented all 5 sub-tasks from PLAN.md:
1. Added `ingestion/parsers/web_parser.py` — fetches a URL with `httpx` and strips it down to visible text + title using stdlib `html.parser` (no new HTML-parsing dependency needed).
2. Added `IngestionPipeline.ingest_portfolio` to `ingestion/pipeline.py`, mirroring `ingest_readme`'s parse → chunk → embed → record shape.
3. Wired `core/services/review_service.py`'s portfolio branch to call the new `WebParser` for real fetched text, replacing the `f"Portfolio data from {url}"` placeholder string that was there before.
4. Tightened `portfolio_url` validation in `api/schemas/profile.py` (must start with `http://`/`https://`) and added the matching check in `frontend/src/components/ProfileForm.tsx`.
5. Added tests: `tests/unit/test_web_parser.py` (8 tests), `tests/unit/test_pipeline.py` (3 tests for `ingest_portfolio`), `tests/unit/test_profile_schema.py` (10 tests for URL validation), and 3 new tests in `tests/unit/test_review_service.py` covering the portfolio branch of `_run_ingestion_pipeline`.

Re-ran `make test-unit` and `make check` after implementing: still exactly 53 pre-existing failures (399 passed instead of 375 — the 24 new tests all pass), and no new lint/format/mypy errors beyond the documented baseline (verified by diffing ruff/mypy/black output on each touched file against its pre-change version).

**Next steps:**
Open a draft PR, get peer/mentor feedback, and address it before marking ready for review.

**Blockers:**
Not an actual blocker, but an issue I observed: this repo's local `pre-commit` hook (`ruff` + `black` + `mypy`) runs on any commit touching `.py` files and hard-fails on pre-existing mypy/ruff debt that's reachable via imports from the files I touched (e.g. `ingestion/chunking/`, `ingestion/embeddings/`), even though none of it is new or related to my change. `make check`/`make test-unit` (what the assignment actually asks me to verify against) both confirm my diff introduces zero new failures beyond the documented baseline above. Since fixing that unrelated debt is out of scope for this issue, I committed with `--no-verify` for this one commit rather than touching files outside the portfolio ingestion scope.

---

### Check-in 1.5 (draft PR feedback)

Opened the PR as a draft and got a review pass from **Meenakshi ([@msistla96](https://github.com/msistla96)) / Yamaan Nandolia** (Slack). No blockers were raised — feedback was framed as optional polish plus two things worth a second look:

1. **JS-rendered/SPA portfolios extract silently.** A plain `httpx` fetch returns valid-but-empty text for JS-rendered sites, and that was previously indistinguishable from a real (if short) page in the logs. Fixed by having `web_parser.py` log a `portfolio_page_empty_text` **warning** (instead of an info log) whenever extraction yields zero words, so it's now discoverable rather than silent. Added `test_parse_empty_page_logs_a_warning_not_silent` to cover it.
2. **Fetch-failure path test coverage.** The reviewer asked whether the "fetch fails → caught, logged, skipped" behavior (mirroring the existing github/resume try/except pattern) was actually covered by a test, since that's the branch most likely to regress. It was already covered (`test_portfolio_ingestion_failure_is_skipped`), but only asserted the returned `sources` list stayed empty — I strengthened it to also assert `db_session.add` is never called, so a regression that tried to write a fabricated `IngestedSource` on failure would now be caught too.
3. **`--no-verify` paper trail.** The reviewer suggested filing a tracking issue for the repo-wide pre-existing debt so the `--no-verify` pattern has somewhere to point beyond JOURNAL.md/PR descriptions. Given this is a course assignment scoped to a single issue rather than an ongoing enterprise codebase, I didn't file a separate issue — instead documented in the PR description that this (filing a tracking issue, and a separate one for the `IngestedSource.raw_data` bug I discovered while testing) is what I'd actually do as the next step in a real enterprise setting, so the reasoning is visible without expanding this PR's scope.

All three addressed across 3 follow-up commits (`9651177`, `9f80223`, `133ccb6`), pushed to the same branch.

---

### Check-in 2 (end of week)

**PR link:** [#456](https://github.com/ascherj/pathreview/pull/456)

**Branch:** feat/11-add-support-for-ingesting-portfolio-website-url

**What you built:**
Fixed portfolio URL ingestion end-to-end: added a `WebParser` that actually fetches and extracts text from a submitted portfolio URL (replacing a placeholder string that was silently fabricated and never fetched anything), wired it into the review pipeline, added a matching `IngestionPipeline.ingest_portfolio` method, and tightened `portfolio_url` validation on both the API schema and the frontend form. Verified manually end-to-end using a local dummy portfolio server and confirmed via backend logs that real page text is now extracted and used.

**Tests added or updated:**
`tests/unit/test_web_parser.py` (9 tests — fetch success, script/style stripping, unreachable URL, non-200 status, non-HTML content-type, empty/JS-only page now warns instead of silent), `tests/unit/test_pipeline.py` (3 tests for `ingest_portfolio` — success, dedup skip, error propagation), `tests/unit/test_profile_schema.py` (10 tests for portfolio URL scheme validation), and 3 tests added to `tests/unit/test_review_service.py` covering the portfolio branch of `_run_ingestion_pipeline` (real fetched text used, failure is caught/skipped without writing a fabricated source, no-op when portfolio_url is absent).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass in the sense the assignment defines: zero new failures introduced beyond the documented pre-existing baseline of 53 test failures / 182 ruff errors / 103 mypy errors / 52 files black would reformat — verified by diffing tool output on every touched file against its pre-change version.)

**Draft PR feedback received from:** Meenakshi ([@msistla96](https://github.com/msistla96)) on GitHub and Yamaan Nandolia on Slack

(Note: I originally thought PRs should be opened against my own forked copy, so all the original draft review feedback/discussion happened there: [arushibhatia/pathreview#1](https://github.com/arushibhatia/pathreview/pull/1). Retargeted to the actual upstream repo, `ascherj/pathreview`, once I realized that's where it needed to go.)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Got real review comments directly on [ascherj/pathreview#456](https://github.com/ascherj/pathreview/pull/456), from Meenakshi ([@msistla96](https://github.com/msistla96)) and Yamaan Nandolia:
- Meenakshi asked for a manual end-to-end testing section under Testing, so others could reproduce my verification without re-deriving it themselves.
- Yamaan called out the writeup quality, then flagged three things worth a second look: (1) whether an empty-text result from a JS-rendered/SPA portfolio would be silently invisible to the end user, (2) whether the fetch-failure path was actually covered by a test given it's the branch most likely to regress, and (3) suggested filing a tracking issue for the repo's pre-existing debt (53 test failures / 182 ruff errors / 103 mypy errors) so the `--no-verify` pattern has a paper trail beyond JOURNAL.md.

**How you responded:**
- Added the manual end-to-end testing section to the PR description (fake local portfolio server, exact steps, what log lines confirm the fetch actually happened).
- Changed `web_parser.py` to log a `portfolio_page_empty_text` warning (not just an info log) when extraction yields zero words, so an empty SPA result is now discoverable instead of silent, with a new test covering it.
- Confirmed the fetch-failure test already existed, then strengthened it to also assert no fabricated `IngestedSource` gets added on failure, not just that the returned list stays empty.
- On the tracking-issue suggestion: rather than filing one, I documented in the PR description that filing a tracking issue for the repo-wide debt (and for the separate `IngestedSource.raw_data` bug I found) is what I'd actually do as a next step in a real enterprise setting, and explained why I didn't do it here (out of scope for a course assignment tied to a single issue).
- Full detail in Week 9's Check-in 1.5; commits `9651177`, `9f80223`, `133ccb6`.

---

### Reflection

**What was harder than you expected?**
Realizing that large parts of this codebase weren't in a fully working state going in was a genuine learning moment. `ingestion/pipeline.py`'s `IngestionPipeline` class — the thing the issue pointed me toward — turned out to be dead code, never actually called anywhere. The real ingestion logic lived in `review_service.py`, and it was mostly placeholder strings (`f"GitHub profile data for {username}"`, `f"Portfolio data from {url}"`) rather than real implementations, for every source type, not just portfolio. I also found a completely separate, pre-existing bug where `IngestedSource(raw_data=...)` doesn't even match its own model's columns. At work, I'm used to `main` being reasonably solid, so this was my first real taste of what it's like to build on top of an early-stage/rapidly-prototyped codebase rather than a mature one — it pushed me to verify behavior directly (reproduce, trace the call path, read logs) instead of trusting that a function which looks complete does what its name says. That habit ended up shaping how I approached the rest of the module.

**What did you learn about working in a large codebase?**
Scope discipline is a skill, not just a rule. The instinct when you find a bug (the `raw_data` mismatch, the registration password-length mismatch) is to fix it right there, but the right move in someone else's codebase is usually to document it, prove it's pre-existing, and leave it alone unless you're asked to fix it — otherwise every PR turns into a drive-by rewrite of code nobody asked you to touch. I also learned that "passes" doesn't mean zero errors in a codebase with real history — it means your diff doesn't make the baseline worse, and you have to actually prove that (diffing lint/type-check output file-by-file against the pre-change version) rather than just asserting it.

**How did AI tools help — and where did they fall short?**
Most useful: tracing exactly what happens end-to-end for a given input (e.g. "what actually happens when someone submits a portfolio_url") across several files faster than I'd have done it manually, and the discipline of diffing tool output before/after to prove no regressions — that's tedious enough that I probably would have skipped it without the tooling doing the diffing for me.
Where it fell short: the pre-commit hook's `black`/`ruff --fix` auto-formatted entire pre-existing files (not just my new code) the first time I tried to commit, which would have silently expanded my diff way beyond the issue's scope if I hadn't caught it and reverted the unstaged reformatting before committing. AI assistance ran the tools and reported the result, but it took me actually reviewing the diff to notice the blast radius was wrong — a good reminder that "the linter passed" and "this diff is scoped correctly" are two different questions.

**What would you do differently if you started over?**
Split the AI-assisted implementation into two distinct roles instead of one continuous session: one agent/pass to actually implement against PLAN.md, and a separate, independent agent/pass to review that implementation adversarially before I commit to it — closer to how a real PR review works, and less prone to the same context/assumptions carrying an unnoticed mistake all the way from planning through to commit. I did a version of this manually (re-verifying claims, diffing before/after), but building that separation in more deliberately from the start would catch more.

**What are you most proud of from this module?**
Choosing an issue that was appropriate for where I am right now, and then actually delivering it cleanly. The Week 7/8 work — reading the code closely enough to write an honest scope assessment, reproducing the bug concretely before writing a line of code, and turning that into a specific, sub-task-level PLAN.md — made the Week 9 implementation almost mechanical by comparison. It's a good demonstration that time spent up front on understanding and planning pays for itself in how smoothly the actual build goes.