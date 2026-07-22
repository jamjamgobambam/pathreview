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

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
Since this is a feature gap rather than a bug, reproducing it meant tracing what happens to a portfolio URL and showing that nothing real ever gets fetched. I searched the codebase for the portfolio path and found that the ingestion is only faked. In core/services/review_service.py, around lines 229 to 252, a profile's portfolio_url gets turned into a hard-coded string, "Portfolio data from" plus the URL, and that string is what gets stored. The site itself is never downloaded. On top of that there's no ingest_portfolio method in ingestion/pipeline.py and no web_parser.py in ingestion/parsers/, so even if the review service wanted to ingest the page, there's nothing to do it. The result is that no real content from the portfolio ever reaches the vector store, which is exactly the gap the issue describes.

**PLAN.md link:** https://github.com/kousalyaa13/pathreview/blob/feat/11-ingesting-portfolio-website-URL/PLAN.md

**Blockers or open questions:**
My main open question is about scope. The placeholder that actually runs during a review lives in core/services/review_service.py, which the issue doesn't list, and that function doesn't call the IngestionPipeline class at all (GitHub and resume are placeholders there too). So I'm not sure whether "done" means just adding ingest_portfolio to the pipeline like the issue says, or also wiring the review service to use it so the feature works end to end. I'll confirm that in Slack. I'm also still unsure how to handle JavaScript-heavy portfolio sites that return almost no text without a real browser, since plain fetching can't render those.