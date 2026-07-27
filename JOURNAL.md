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