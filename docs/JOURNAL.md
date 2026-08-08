## Week 7 — Issue selection

**Issue link:** [issue link](https://github.com/ascherj/pathreview/issues/11)

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
This is a feature to allow for ingesting a portfolio website url. A pipeline is required to take the portfolio website url, extract contents and include it in the vector store. The vector store should be alognside GitHub and resume data.

**Branch name:** feat/11-add-ingestion-support-for-portfolio-url

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Is This Issue Right for Me? — Checklist

### Part 1 — Understanding the Issue

- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x]  I've located the relevant files and confirmed they exist in the codebase.
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

### Part 2 — Tier Fit

- [x] The tier is a realistic match for where I am right now:
  - If this is my first open source contribution: I'm choosing Tier 1.
  - If I've contributed to large codebases before: Tier 2 or 3 is fair game.
  - I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

### Part 3 — Codebase Readiness

- [x] I've found and read the specific code the issue references (not just the file — the function or section).
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- [x] I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [95002dc — docs: reproduce issue #11 — confirm portfolio_url ingestion gap](https://github.com/narayanansriram/pathreview/commit/95002dc)

**Reproduction summary:**
Since this is a feature gap rather than a bug, I reproduced it by writing `scripts/check_portfolio_ingestion.py`, which queries the local dev database directly. The `profiles` table already has 4 rows with a `portfolio_url` set (e.g. `https://yasio.dev/`), confirming the field is accepted and persisted end-to-end at the API/schema/DB layer. But the `ingested_sources` table has 0 rows with `source_type='web'` — confirming that `portfolio_url` is never passed to the ingestion pipeline, so no chunks are ever extracted, embedded, or stored for it, unlike GitHub/resume data.

**Command run:**
```
.venv/bin/python -m scripts.check_portfolio_ingestion
```

**Output:**
```
Profiles with a portfolio_url set: 4
  - e953c1f6-30cf-488a-9d36-03760e496adb: https://user1.dev
  - 7abbe7f5-69af-40c9-9f1f-2754f22bc27a: https://user2.portfolio
  - bd3ae3df-71dd-481d-9726-d3773b3cc206: https://user3.io
  - 1e7f5e95-2284-45c4-b8a7-b47b03bcdbd9: https://yasio.dev/

IngestedSource rows with source_type='web': 0

Reproduction confirmed: portfolio_url is accepted and stored on Profile, but no IngestedSource has ever been created for it — the ingestion pipeline is never invoked for portfolio URLs (see PLAN.md).
```

**PLAN.md link:** [PLAN.md](../PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
`IngestionPipeline` currently has no live caller anywhere in the app — resume and readme ingestion aren't wired into any route either, only stored directly on the `Profile` row. Need to confirm with mentors/instructors whether wiring `ingest_portfolio_url` into `api/routes/profiles.py` is expected to also surface/fix this broader wiring gap, or whether it's acceptable to scope this issue narrowly to the portfolio-URL path only.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md's "Plan" section are implemented:

1. `ingestion/parsers/web_page_parser.py` — new `WebPageParser` fetches a URL via `httpx` (10s timeout, follows redirects), validates `Content-Type` is HTML, and extracts text with `BeautifulSoup` (stripping `script`/`style`/`nav`/`footer`/`noscript` tags).
2. `ingestion/pipeline.py` — added `ingest_portfolio_url(profile_id, url)`, following the same structure as `ingest_readme`. Also completed `_check_skip()` and `_record_ingested_source()`, which were previously stub/placeholder methods — they now actually query and persist to the `ingested_sources` table via SQLAlchemy, which resume/readme/repo ingestion benefit from too.
3. `ingestion/chunking/strategy_selector.py` — added a `"web"` branch. Deviated from PLAN.md's suggestion of `StructuralChunker`: web pages are stripped to plain text with no markdown headings, so the heading-based structural chunker would produce zero chunks. Mapped to `SemanticChunker` instead, with a comment explaining why.
4. `api/routes/profiles.py` — wired `ingest_portfolio_url` into both `create_profile_endpoint` and `update_profile_endpoint` via a new `get_ingestion_pipeline` FastAPI dependency. Ingestion runs best-effort: a slow or unreachable portfolio site logs a warning but does not fail profile creation/update, since there's no background job infra in this codebase to defer it to.
5. `pyproject.toml` — added `beautifulsoup4` as a dependency for real HTML parsing (in place of a regex-only fallback).

New tests: `tests/unit/test_web_page_parser.py` (8 tests: HTML stripping, empty/SPA pages, bytes input, invalid content type, missing title, successful fetch, HTTP error, non-HTML content type) and `tests/unit/test_pipeline.py` (4 tests: happy path, skip-if-already-ingested via content hash, fetch failure propagation, no-extractable-text edge case). All 12 pass.

Verified no regressions: `make test-unit` baseline (before this work) was 57 failed / 383 passed; after, 53 failed / 387 passed — the same pre-existing failures, minus 4 that only failed because this code didn't exist yet. `make check` deltas (2 new mypy findings, a few new ruff `B008` instances) are all the same pre-existing conventions already used throughout `api/routes/profiles.py` (untyped `db` params, `Depends()` in argument defaults) — no new categories of lint/type debt introduced.

**Next steps:**
- Run `make check` in full (lint + format + typecheck) one more time across the whole repo to confirm.
- Read `docs/CONTRIBUTING.md` and double check branch naming, commit message, and docstring conventions before opening the PR.
- Open a draft PR early and ask for peer/mentor feedback per the Week 9 instructions.
- Fill in the PR template and write the description, calling out the pre-existing failures explicitly as instructed.

**Blockers:**
None currently — the open question from Week 8 (whether to also fix the broader "pipeline has no caller" gap for resume/readme) resolved itself naturally: completing `_check_skip`/`_record_ingested_source` for real was necessary for portfolio-URL dedup to work at all, so it also benefits the other source types as a side effect, without expanding scope beyond issue #11's route-wiring for `portfolio_url`.

---

### Check-in 2 (end of week)

**PR link:** [ascherj/pathreview#506](https://github.com/ascherj/pathreview/pull/506)

**Branch:** `feat/11-add-ingestion-support-for-portfolio-url`

**What you built:**
Added a `WebPageParser` that fetches a portfolio URL via `httpx` and extracts text with `BeautifulSoup`, wired a new `ingest_portfolio_url` method into `IngestionPipeline`, and called it from the profile create/update routes as a best-effort step so a slow or unreachable portfolio site never fails profile creation. Also completed `_check_skip`/`_record_ingested_source`, which were previously stub methods, so content-hash dedup actually works now.

**Tests added or updated:**
`tests/unit/test_web_page_parser.py` (8 new tests: HTML stripping, empty/SPA pages, bytes input, invalid content type, missing title, successful fetch, HTTP error, non-HTML content type) and `tests/unit/test_pipeline.py` (4 new tests: happy path, skip-if-already-ingested, fetch failure propagation, no-extractable-text edge case). All 12 pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!-- Note: both are "passes" in the course's documented-pre-existing-failures sense, not a literal zero-error run — make test-unit has 53 pre-existing failures on main (387 passed, no new failures); make check has pre-existing ruff (162) and mypy (100) errors repo-wide, unrelated to this change and documented in the PR's Notes for Reviewers (PR #506). -->

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments have come in on [PR #506](https://github.com/ascherj/pathreview/pull/506) as of this writing. Per the Su26 note, reviewer feedback isn't a live feature this term, so this is expected rather than a gap in outreach.

**How you responded:**
N/A — nothing to respond to yet.

---

### Reflection

**What was harder than you expected?**
Distinguishing "my bug" from "already broken" was the hardest part of Week 9. When the pre-commit hook failed on my commit, it dumped 49 mypy errors across 11 files — but I'd only touched `ingestion/pipeline.py` and `api/routes/profiles.py`. It wasn't obvious at first whether those errors were things I'd introduced or debt that was already there. I had to learn that mypy's pre-commit hook follows imports, so touching a file that imports `profile_service.py` or `vector_store.py` re-surfaces every pre-existing untyped function in those files too — even though I never edited them. The only way I found to confirm what was actually mine was `git stash`-ing my changes and re-running the same lint/type/test commands against the unmodified baseline, then diffing the counts. That technique — proving a failure is pre-existing rather than assuming it — was the single most useful workflow habit I picked up this module.

**What did you learn about working in a large codebase?**
In my own projects, if a field exists on a model, it's usually because I just wired it up — there's no gap between "accepted" and "used." Here, `portfolio_url` had already been validated by Pydantic, persisted by SQLAlchemy, and returned in API responses. Four real seeded profiles even had real URLs saved. Everything *looked* done. But none of that meant the feature actually worked — the ingestion pipeline never touched it. I only found this by directly querying the database (`scripts/check_portfolio_ingestion.py`) and seeing `profiles` had rows with `portfolio_url` set while `ingested_sources` had zero rows with `source_type='web'`. In a large, already-built codebase, a field being present, typed, and validated is not evidence that it's connected to anything — you have to trace the actual data flow end-to-end, because half-finished plumbing looks identical to finished plumbing from the schema alone.

**How did AI tools help — and where did they fall short?**
AI was most useful when I hit environment failures I had no context for — the pre-commit `mypy` hook failing to install `types-redis` because `cryptography`'s Rust build couldn't find OpenSSL, which turned out to be caused by an outdated Homebrew (bundling Ruby 2.6, unable to parse modern formula syntax) and Command Line Tools from 2021. Diagnosing that chain — Rosetta emulation → stale CLT → broken Homebrew Ruby → missing OpenSSL — would have taken me hours of searching; the AI worked through it step by step in the same session.
It fell short on scope judgment: when I asked it to "fix everything mypy flags" to get past a failing pre-commit hook, it started adding type annotations across seven files completely unrelated to portfolio URL ingestion — `profile_service.py`, `vector_store.py`, `semantic_chunker.py`, etc. Technically it was doing what I asked, but I had to step back, recognize the scope had ballooned past what issue #11 actually needed, and explicitly tell it to revert those changes and use `--no-verify` on the pre-existing debt instead. The lesson: AI will happily go as far as your literal instruction lets it, so scope discipline has to come from me, not from it.

**What would you do differently if you started over?**
I'd dig into `IngestionPipeline`'s actual callers during Week 7 issue selection, not wait until Week 8's reproduction step to discover it. The "Is This Issue Right for Me?" checklist asks whether you understand what "done" looks like and whether you've read the relevant code — I checked those boxes based on reading `ingestion/pipeline.py` in isolation, without checking whether anything in `api/routes/` actually called it. It turned out none of `ingest_resume`/`ingest_readme`/`ingest_repo_metadata` had a live caller either, and `_check_skip`/`_record_ingested_source` were stubs. That context — that this wasn't just "add one method," it was "add one method into a pipeline nobody invokes, with dedup logic that doesn't work yet" — would have changed my time estimate and Tier assessment from the start, instead of surfacing as a mid-module surprise.

**What are you most proud of from this module?**
Proving the reproduction with real data instead of just asserting the bug existed. Rather than saying "portfolio_url ingestion doesn't work," I wrote `scripts/check_portfolio_ingestion.py` and pointed to the actual database state: 4 seeded profiles with a real `portfolio_url` set, and 0 `IngestedSource` rows with `source_type='web'`. That's evidence anyone — a reviewer, a mentor, my future self — could re-run and get the same result. It turned "I think this is broken" into "here's the query, here's the output, here's exactly where the gap is," which is the same standard I'd want applied to a bug report I received myself.