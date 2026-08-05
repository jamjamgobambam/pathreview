# Solution plan

**Issue:** [Add support for ingesting a portfolio website URL (#11)](https://github.com/ascherj/pathreview/issues/11)

### Understand

`portfolio_url` is captured in `ProfileCreate`/`ProfileUpdate` and stored on
the `Profile` model, but nothing in the ingestion layer ever fetches or
parses it. Expected behavior per the issue: submitting a portfolio URL
should result in its bio/project text being fetched, extracted, chunked,
embedded, and stored in the vector store alongside resume and GitHub data,
so the review agent can reference it. Actual behavior: the URL is inert —
just a string sitting in Postgres. The one place code *mentions* portfolio
ingestion (`core/services/review_service.py::_run_ingestion_pipeline`) is an
explicit placeholder that fabricates a string instead of fetching real
content, and never touches the vector store. See `docs/issue-11-repro.md`
for the full reproduction trail.

### Map

- `ingestion/parsers/base.py` — existing `BaseParser`/`ParseResult`
  interface to implement against (no changes needed).
- `ingestion/parsers/web_parser.py` (new) — HTML fetch + text extraction,
  mirroring `ResumeParser`/`ReadmeParser`.
- `ingestion/pipeline.py` — add `IngestionPipeline.ingest_portfolio()`,
  following the shape of `ingest_resume`/`ingest_readme`/`ingest_repo_metadata`.
- `api/schemas/profile.py` — validate `portfolio_url` is a well-formed
  http(s) URL before it's ever stored.
- `api/dependencies/ingestion.py` (new) — builds the `IngestionPipeline`
  (vector store + embedding provider) so a route can call `ingest_portfolio`.
- `api/routes/profiles.py` — trigger `ingest_portfolio` in the background on
  profile create/update.
- `core/services/review_service.py` — **not touched in this pass**; still
  holds the review-generation-time placeholder for portfolio data (see
  Risks below).

### Plan

1. Build `WebParser` (`ingestion/parsers/web_parser.py`): strip boilerplate
   tags (`script`/`style`/`nav`/`footer`/`header`/`aside`), extract bio and
   project text plus lightweight metadata (title, section hints), and guard
   against SSRF (block non-http(s) schemes and loopback/private/link-local
   addresses, including on redirect hops).
2. Add `IngestionPipeline.ingest_portfolio(profile_id, url)`: fetch → parse
   → chunk (reusing `StrategySelector`) → embed → store, matching the
   skip/hash/record pattern of the other `ingest_*` methods.
3. Validate `portfolio_url` in `ProfileCreate`/`ProfileUpdate` (reject
   non-http(s) or malformed values) so bad input never reaches the pipeline.
4. Wire a `BackgroundTasks` trigger in `api/routes/profiles.py` so profile
   create/update kicks off ingestion without blocking the request, backed by
   a cached pipeline factory in `api/dependencies/ingestion.py`.
5. Add unit tests for the parser (extraction, boilerplate stripping, error
   cases), the SSRF guard (blocked hosts/schemes, redirect re-validation),
   and pipeline tests for metadata sanitization and stale-chunk cleanup on
   re-ingestion.

### Inputs & outputs

- **Input:** a `portfolio_url` string (from `ProfileCreate`/`ProfileUpdate`)
  and the `profile_id` it belongs to.
- **Output:** chunks of cleaned portfolio text, embedded and upserted into
  the ChromaDB collection, tagged with `source_type="portfolio"` and
  `profile_id`, retrievable the same way resume/README chunks are.
- **Side effects:** an `IngestResult` (chunk count, skip status) is logged;
  the HTTP response shape is unchanged — ingestion runs after the response
  is already prepared, in the background.

### Risks & unknowns

- **SSRF via redirects:** a public URL can redirect to an internal address
  (e.g. the cloud metadata IP `169.254.169.254`); `httpx`'s default
  `follow_redirects=True` does not re-check the SSRF guard on each hop, so
  redirects need to be followed manually with re-validation at every step.
- **ChromaDB metadata constraints:** `extracted_sections` is naturally a
  list and `title` can be `None`; ChromaDB only accepts scalar metadata
  values, so both need sanitizing before every vector-store write or
  ingestion fails silently at that step.
- **Stale vectors on URL change:** without deleting a profile's prior
  portfolio chunks before re-ingesting, changing the URL leaves orphaned old
  content behind, and re-ingesting the same URL risks colliding on
  duplicate chunk IDs.
- **Known gap, intentionally not fixed in this pass:**
  `core/services/review_service.py::_run_ingestion_pipeline` (used at
  review-generation time, a separate code path from profile-creation-time
  ingestion) still contains a hardcoded placeholder for portfolio data, and
  `_run_rag_retrieval_generation` doesn't query the vector store at all —
  it returns fully hardcoded feedback sections. So even with real ingestion
  in place, the review-generation flow doesn't yet surface it end-to-end.
  This looks like broader, pre-existing scaffolding (the same placeholder
  pattern also covers `github` and `resume`), likely a separate issue's
  scope — flagging it here since it affects whether this fix is visible to
  a user in the product, not just in the vector store.
- **No existing pipeline instantiation anywhere in the app** before this
  change — `IngestionPipeline` had never been wired up with real
  dependencies (vector store, embedding provider), so that plumbing had to
  be built from scratch in `api/dependencies/ingestion.py`.

### Edge cases

- Non-existent / unreachable URL (DNS failure, connection refused, timeout)
  → fails gracefully and logs, without crashing profile creation.
- Non-HTML response (JSON API, PDF, etc.) → rejected with a clear error.
- Empty page, or a JS-only SPA shell with no server-rendered text → raises
  rather than silently storing an empty embedding.
- Extremely large pages → size-capped before parsing.
- URL pointing at localhost, a private network address, or the cloud
  metadata endpoint → blocked outright, including when reached via redirect.
- User updates `portfolio_url` to a new site → old portfolio chunks for
  that profile are removed, not just appended to.
- User submits the exact same URL twice → does not create duplicate chunk
  IDs in the vector store.
