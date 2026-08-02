## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Right now, PathReview can ingest data from a resume, a GitHub profile, and repos. This issue adds a fourth source: a user's personal portfolio website. The user pastes a URL like https://janedoe.dev, and the system should fetch that web page, pull out the meaningful text (their bio, project write-ups), and feed it into the same "vector store" that powers the AI feedback. This allows the AI to reference their portfolio when reviewing them.

I would have to add an ingest_portfolio() method that mirrors the existing ingest_resume / ingest_readme methods almost line-for-line: generate a source_id, check-if-already-ingested, call the new parser, chunk, embed, and record. 

**Branch name:** feat/11-ingesting-portfolio-website-URL                                                    

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kousalyaa13/pathreview/commit/2796474c747de3f6e68259dba6abec66273f3837

**Reproduction summary:**
Since this is a feature gap rather than a bug, reproducing it meant tracing what happens to a portfolio URL and showing that nothing real ever gets fetched. I searched the codebase for the portfolio path and found that the ingestion is only faked. In core/services/review_service.py, around lines 229 to 252, a profile's portfolio_url gets turned into a hard-coded string, "Portfolio data from" plus the URL, and that string is what gets stored. The site itself is never downloaded. On top of that there's no ingest_portfolio method in ingestion/pipeline.py and no web_parser.py in ingestion/parsers/, so even if the review service wanted to ingest the page, there's nothing to do it. The result is that no real content from the portfolio ever reaches the vector store, which is exactly the gap the issue describes.

**PLAN.md link:** https://github.com/kousalyaa13/pathreview/blob/feat/11-ingesting-portfolio-website-URL/PLAN.md

**Blockers or open questions:**
My main open question is about scope. The placeholder that actually runs during a review lives in core/services/review_service.py, which the issue doesn't list, and that function doesn't call the IngestionPipeline class at all (GitHub and resume are placeholders there too). So I'm not sure whether "done" means just adding ingest_portfolio to the pipeline like the issue says, or also wiring the review service to use it so the feature works end to end. I'll confirm that in Slack. I'm also still unsure how to handle JavaScript-heavy portfolio sites that return almost no text without a real browser, since plain fetching can't render those.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've built the whole feature and all five sub-tasks from PLAN.md are done. I added a WebParser in ingestion/parsers/web_parser.py that fetches a portfolio page (with a timeout, redirect handling, an HTML content-type check, and a size cap) and extracts the readable text while stripping out script, style, nav, and footer noise. I added an ingest_portfolio method to the pipeline that mirrors the existing ingest_readme flow, and I added a validator on the profile schema so a portfolio_url without http(s):// is rejected early. I also pulled in beautifulsoup4 as a dependency. Everything is committed in three commits, and I wrote 24 tests across three files that all pass.

Before starting I ran the test suite and recorded that the repo already has 53 failing unit tests that have nothing to do with my issue. After my changes there are still exactly 53 failures and zero new ones, and my 24 tests pass on top of that.

**Next steps:**
Open a draft PR and get a classmate or mentor to review it in Slack. Confirm with the cohort whether the PR should target the upstream repo or my fork. Decide, based on feedback, whether to also wire core/services/review_service.py to actually call the new pipeline so the feature works end to end, or leave that as a documented follow-up. Then address any feedback, mark the PR ready for review, and fill in Check-in 2 with the PR link.

**Blockers:**
The main open question is scope: the placeholder that runs during a real review is in review_service.py, which the issue doesn't list and which doesn't call the ingestion pipeline at all. I am going to be confirming in Slack whether wiring that up is expected for this issue or belongs in a separate PR.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/571

**Branch:** feat/11-ingesting-portfolio-website-URL

**What you built:**
Portfolio website ingestion. A submitted portfolio URL is now fetched and its readable text (bio, project descriptions) is extracted, chunked, embedded, and stored in the vector store alongside the resume, GitHub, and repo sources, so the AI reviewer can reference what's actually on the site. Before this change the app stored a hard-coded placeholder string instead of ever visiting the page.

**Tests added or updated:**
Three new files. tests/unit/test_web_parser.py (10 tests) covers text extraction, noise-stripping, and fetch error handling. tests/unit/test_pipeline.py (4 tests) covers the ingest_portfolio success, skip, metadata, and fetch-error paths. tests/unit/test_profile_schema.py (10 tests) covers portfolio_url validation for valid, empty, and invalid URLs.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both in the sense the cohort defined for a repo with documented pre-existing failures: my changes introduce zero new failures. The 53 pre-existing test failures and the pre-existing mypy errors are documented in the PR description.)

**Draft PR feedback received from:** none — I posted the draft PR in Slack for review, but no one left feedback before the deadline.