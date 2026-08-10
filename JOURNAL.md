## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The profile flow already accepts a portfolio URL, but the codebase does not actually fetch and ingest the website content yet. That means portfolio sites are collected as metadata only, without any text extraction for embedding or review generation. A successful fix would add a parser or ingestion path that pulls relevant page content from the portfolio URL and stores it alongside the other ingested sources. This would let portfolio websites contribute real evidence to the review pipeline instead of being ignored.

**Scope reasoning:**
This issue is a good fit for Week 7 because it is focused on a single ingestion path in the review pipeline rather than a broad redesign. The change can be implemented and verified through unit tests plus a local smoke test without touching unrelated features. The work also has clear acceptance criteria: a portfolio URL should produce ingested content that can be persisted and used downstream.

**Branch name:** feat/11-portfolio-website-ingestion

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/maninampally/pathreview/commit/7df4ff02dce73f7adec331f4845e70eed6d60f7f

**Reproduction summary:**
Confirmed the gap by diffing `core/services/review_service.py` against the pre-fix commit (`0024684`): the portfolio branch of `_run_ingestion_pipeline` only wrote a hardcoded placeholder string (`f"Portfolio data from {profile.portfolio_url}"`) into `IngestedSource`, never fetching the page. Verified the fetch/parse path works by serving `tmp/portfolio_site/index.html` locally and pointing `WebParser.parse()` at it over real HTTP (not a mock) — confirmed it extracts visible text ("Local Portfolio", "Example portfolio content...", "Built with Python, FastAPI, and React.") and the page title, while skipping `<script>`/`<style>` content.

**PLAN.md link:** https://github.com/maninampally/pathreview/blob/feat/11-portfolio-website-ingestion/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Unclear how JS-rendered portfolio sites (client-side rendered SPAs) should be handled — `httpx.get` only sees server-rendered HTML, and the static local fixture doesn't exercise that case. See Risks & unknowns in PLAN.md.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are done: `_VisibleTextExtractor` strips `<script>`/`<style>`/`<noscript>` and captures `<title>`; `WebParser.parse()` fetches via `httpx.get`, validates input, raises on non-2xx, and computes `content_hash`/`word_count`; `_run_ingestion_pipeline`'s portfolio branch in `core/services/review_service.py` now calls `WebParser` instead of writing a placeholder string, and `IngestedSource` fields are aligned across the github/portfolio/resume branches; unit tests added in `tests/unit/test_web_parser.py` and `tests/unit/test_review_service.py`; manually smoke-tested against a local static fixture over real HTTP (see Week 8 entry).

**Next steps:**
Ran `make test-unit` (25/25 new/updated tests pass, 394 total passing) and `make check` — fixed a few black/ruff/mypy issues in the new `web_parser.py`/`test_web_parser.py` files (missing trailing newline, nested `with`, untyped `handle_starttag` param). Confirmed the remaining 40 test failures and the mypy/ruff issues in `review_service.py`/`test_review_service.py` are pre-existing and unrelated (same errors present at the pre-fix commit). Remaining: commit these fixes, push the branch, open a draft PR, request peer/mentor review in Slack, then finalize.

**Blockers:**
None blocking. Open question carried from Week 8: how JS-rendered (SPA) portfolio sites should be handled, since `httpx.get` only returns server-rendered HTML — not addressed in this pass, documented as a known limitation.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/667

**Branch:** `feat/11-portfolio-website-ingestion`

**What you built:**
A `WebParser` that fetches a candidate's portfolio URL over HTTP and extracts its visible text and title (skipping `<script>`/`<style>`/`<noscript>`), replacing the hardcoded placeholder string that `_run_ingestion_pipeline()` previously stored. Real extracted content and a `content_hash` now flow into `IngestedSource` for the portfolio branch, giving downstream RAG/agent steps actual evidence from the candidate's site.

**Tests added or updated:**
`tests/unit/test_web_parser.py` (new) — visible-text extraction, title fallback, bytes input, invalid URL, HTTP error propagation. `tests/unit/test_review_service.py` (updated) — asserts `_run_ingestion_pipeline` calls `WebParser` and stores real extracted text/hash for the portfolio source.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(both pass for the code touched in this PR; 40 pre-existing test failures and pre-existing lint/mypy issues elsewhere in the codebase are unrelated and unchanged from before this fix — documented in the PR description)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments on https://github.com/ascherj/pathreview/pull/667 by the end of Week 10 (Su26: reviewer feedback is not provided this term). Re-checked the PR; still open with no review thread to respond to.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Separating *my* failures from the repo’s existing noise. `make test-unit` / `make check` still reported ~40 failing tests and lint/mypy issues in `review_service.py` / `test_review_service.py` that were already present at the pre-fix commit (`0024684`). I spent real time bisecting and comparing against that baseline before I trusted that my `WebParser` / portfolio-branch changes were clean. The other surprise was how little of the “portfolio URL” path actually did work: the UI collected the URL, but `_run_ingestion_pipeline` only stored `f"Portfolio data from {profile.portfolio_url}"` — so reproducing the bug meant proving a missing fetch/parse path, not a flaky network call.

**What did you learn about working in a large codebase?**
You can’t treat the repo like a greenfield app. I had to follow existing contracts (`BaseParser` / `ParseResult`), mirror how other ingestion branches populate `IngestedSource` (`source_type`, `source_url`, `content_hash`), and keep the portfolio change scoped so it didn’t drag in SPA rendering, SSRF hardening, or pipeline error UX. In my own projects I’d often widen scope mid-build; here the right move was a focused parser + wiring + tests, and documenting known limits (JS-rendered portfolios, timeouts swallowed by a broad `except Exception`) in `PLAN.md` instead of “fixing” everything in one PR.

**How did AI tools help — and where did they fall short?**
AI helped most for scaffolding: `HTMLParser` subclass sketch, `httpx` fetch/error patterns, and first drafts of unit tests with mocked `httpx.get`. It fell short on *ground truth* in this repo — e.g. whether failures were mine vs pre-existing, and whether a static fixture smoke test was enough. I still had to diff against the pre-fix commit, run the full unit suite, serve `tmp/portfolio_site/index.html` over real HTTP, and decide myself that SPA/client-rendered portfolios were out of scope rather than inventing a headless browser solution the AI suggested as “easy.”

**What would you do differently if you started over?**
I’d establish the pre-existing failure baseline on day one of reproduction (run `make test-unit` / `make check` on the pre-fix commit and save the output) so Week 9 self-review didn’t turn into detective work. I’d also pick a slightly smaller first slice earlier — land `WebParser` + tests first, then the `review_service` wiring — instead of holding the full five-task plan until everything landed together. For issue selection, I’d still choose this Tier 2 ingestion gap, but I’d write the SPA limitation into the issue/PR description up front so reviewers aren’t surprised.

**What are you most proud of from this module?**
The reproduction discipline: proving the gap with a real HTTP round-trip against a local static portfolio page (not only mocks), then replacing the placeholder with extracted visible text + `content_hash` so the portfolio `IngestedSource` finally carries evidence the rest of the pipeline can use. That felt like a real contribution path, not just “tests pass on my laptop.”