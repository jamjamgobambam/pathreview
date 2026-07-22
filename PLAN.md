## Solution plan

**Issue:** Add support for ingesting a portfolio website URL

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The portfolio URL gets saved on the profile, but nothing ever fetches or reads it. The form, the profile routes, and the DB all handle `portfolio_url` fine — it's just never used. The reason is that `IngestionPipeline` only has `ingest_resume`, `ingest_readme`, and `ingest_repo_metadata`. There's no `ingest_portfolio` and no `web_parser.py`. It should work like the other sources: fetch the page, parse the bio/project text, chunk it, and embed it so it actually feeds into RAG.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `ingestion/parsers/web_parser.py` — new `WebParser`, based on `resume_parser.py`
- `ingestion/pipeline.py` — add `ingest_portfolio(profile_id, url)`
- `core/services/profile_service.py` — call ingestion when a profile is saved with a portfolio URL
- `tests/unit/test_pipeline.py` — tests for `ingest_portfolio`

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Write `WebParser` — fetch the URL, strip boilerplate, pull out the readable text
2. Add `ingest_portfolio` to the pipeline, following the same shape as `ingest_resume`
3. Hook it into `profile_service.py` so saving a profile with a portfolio URL kicks off ingestion
4. Make `_record_ingested_source` actually write to the DB instead of just logging, so dedup works
5. Turn the reproduction stubs in `test_web_parser.py` into real tests

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Takes a `profile_id` and `portfolio_url`. Produces the same `IngestResult` as the other ingest methods, and writes new embeddings into the vector store.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- External sites are unreliable — timeouts, redirects, weird content types. Needs to fail quietly, not break profile creation.
- Haven't decided if ingestion should run inline on save or get pushed to a background job.

### Edge cases
What inputs or states should your fix handle gracefully?

- No portfolio URL — just skip it
- URL is down or errors out — log it, move on
- URL isn't actually an HTML page (PDF, image, etc.)
- Same URL submitted twice with no changes — shouldn't re-embed
- Portfolio content changes later — should pick that up instead of skipping forever
