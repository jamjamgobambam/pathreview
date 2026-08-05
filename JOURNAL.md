## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

I picked Tier 2 because I have previously built RAG pipeline and I can mirror existing pipline for resume to build new feature

**Problem summary:**
The is no existing ingestion pipeline for the portfolio submitted through the URL. The successful implemention would fetch the page content, extract relevant text (bio, project descriptions), and include it in the vector store. The parts of database that are involved: 
ingestion/parsers/ (new web_parser.py)
ingestion/pipeline.py
api/schemas/profile.py

**Branch name:** feat/11-portfolio-url-ingestion

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Tanya703/pathreview/commit/67149a3d194a6364d27765e0a0f69f7120b34eb3

**Reproduction summary:**
I added `tests/unit/test_web_parser.py`, which imports `ingestion.parsers.web_parser.WebParser` and calls `IngestionPipeline.ingest_portfolio(...)`. Running `pytest tests/unit/test_web_parser.py -v` confirmed the gap: the import fails with `ModuleNotFoundError: No module named 'ingestion.parsers.web_parser'`, and the pipeline test fails with `AssertionError` because `IngestionPipeline` has no `ingest_portfolio` method. This confirms that although the UI, API, and DB already accept and store a profile's `portfolio_url`, nothing ever fetches or ingests that page's content into the vector store.

**PLAN.md link:** https://github.com/Tanya703/pathreview/blob/feat/11-portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
When I tried replicating the issue through the UI, I couldn't see any ingested sources in the database after submitting a new profile — but all the info was saved correctly in `profiles`.  Is there a bug? Typeerror with ingestion? 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I have implemented a Webparser part: 1. Write `WebParser` — fetch the URL, strip boilerplate, pull out the readable text

**Next steps:**
[What are you working on for the rest of the week?]
I am looking to get steps done:
2. Add `ingest_portfolio` to the pipeline, following the same shape as `ingest_resume`
3. Hook it into `profile_service.py` so saving a profile with a portfolio URL kicks off ingestion
4. Make `_record_ingested_source` actually write to the DB instead of just logging, so dedup works
5. Turn the reproduction stubs in `test_web_parser.py` into real tests

**Blockers:**
[Anything slowing you down? Or leave blank.]
I need to figure out all files I need to update and add URL ingestion

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/450

**Branch:** feat/11-portfolio-url-ingestion


**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I build a portfolio URL ingestion: a new WebParse that fetches porfolio page and extracts text and an ingest_portfolio method that runs tesx through the same chenk and embed flow. I wired this into profile_service.py so saving a profile with a portfolio_url automatically triggers ingestion in the background, failing quietly if the site is down or unparseable. You also fixed _record_ingested_source/_check_skip to actually read and write the IngestedSource table.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
14 tests were added
WebParser.parse() is tested for extracting readable text from portfolio HTML, stripping script/style/nav boilerplate, capturing title and word-count metadata, handling bytes input, and rejecting invalid content types. WebParser.fetch() is tested for a successful fetch, an HTTP/connection error, and a non-HTML content type, all raising ValueError appropriately. IngestionPipeline.ingest_portfolio() is tested end-to-end (fetch → parse → chunk → embed → DB record), for skipping re-ingestion of unchanged content (dedup), and for propagating exceptions when a fetch fails.

**Self-review confirmation:** [ x] make check passes  [x ] make test-unit passes

**Draft PR feedback received from:**  "none"

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [ x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
One area to focus on going forward is tightening the connection between your tests and the actual production code paths. Your test descriptions mention 14 tests covering fetch, parse, chunking, and dedup scenarios, which is great coverage in principle. However, when tests rely heavily on mocking every dependency (the HTTP client, the database session, the vector store, the embedding provider), it's easy to end up testing that your mocks behave correctly rather than that your code handles real-world edge cases. A practical habit to build: after writing mock-heavy unit tests, ask yourself "what would break in production that these tests wouldn't catch?" For example, testing that WebParser.parse() strips <script> and <nav> tags is valuable, but also consider whether your fetch timeout, redirect-following behavior, or character encoding handling would survive contact with a real portfolio site. Even one or two tests with realistic HTML fixtures (saved from actual portfolio pages) can catch parsing bugs that synthetic test HTML misses. This kind of thinking — bridging the gap between test confidence and production reliability — is one of the most transferable skills in professional engineering work.



**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
I need to update the tests to cover edge cases.
---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
Navigating and understanding the codebase was harder than expected. It required more time to trace where methods are being imported from, undetrstanding archetecture of the app. This experience also taught me to be more thoughtful on the way I leverage Claude and parts that I should do by myself.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
When working in a large codebase, adding a small feature can result into a need to update a lot of other files which requires understanding of how all the pieces of the codebase fit together.When contributing to someone elso project you need to pay attention to contribution guidelines, align the formate of your code with the codebase format.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?] Claude was very hrlpful with understanding the structure of the codebase. It also provided a nice draft of the solution. Claude fell short when generating test for new feature. It didn't cover edge cases and would need more precise promting.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?] I rushed through understanding the problem and codebase which slowed me down when it came to implementation as it needed multiple revisions. Next time I would spend more time using Claude to understand codebase. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am proud of being able to leverage Claude to contribute to large codebases