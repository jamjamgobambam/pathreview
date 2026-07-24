## Solution plan

**Issue:** Add support for ingesting a portfolio website URL — [ascherj/pathreview#11](https://github.com/ascherj/pathreview/issues/11)

### Understand

**Expected behavior:** When a user submits a `portfolio_url` on profile creation (or update), the app should fetch that page, extract its text content, chunk and embed it, and store it in the vector store alongside the existing GitHub (readme/repo) and resume data — so RAG queries can draw on portfolio content too.

**Actual behavior:** `portfolio_url` is already accepted end-to-end at the API/schema/DB layer (`ProfileCreate`/`ProfileUpdate` in `api/schemas/profile.py`, `Profile.portfolio_url` in `core/models/profile.py`), but it is never passed to the ingestion pipeline. `IngestionPipeline` (`ingestion/pipeline.py`) has `ingest_resume`, `ingest_readme`, and `ingest_repo_metadata`, but no `ingest_portfolio_url` method, and no route calls the pipeline at all today. So the root cause isn't a bug — it's a missing pipeline method plus missing wiring from the API route into that pipeline.

**Root cause:** `IngestionPipeline` has no `ingest_portfolio_url` method, there's no parser to fetch/extract a webpage's content, and `api/routes/profiles.py`'s `create_profile_endpoint` never invokes ingestion for the portfolio URL (or for resume/readme either — the pipeline currently has no live caller anywhere in the app, only `portfolio_url`/`resume_text` fields being stored directly on the `Profile` row).

### Map

Files/functions I expect to touch:

- **New:** `ingestion/parsers/web_page_parser.py` — `WebPageParser(BaseParser)`, following the shape of `ingestion/parsers/readme_parser.py` and `ingestion/parsers/resume_parser.py`. Fetches the URL via `httpx` (same pattern as `agent/tools/github_tool.py:93`, `httpx.get(..., timeout=10.0)` + `except httpx.HTTPStatusError`), then extracts text (regex HTML-strip like `resume_parser.py:120`, or `BeautifulSoup` if added as a dependency).
- **Edit:** `ingestion/pipeline.py` — add `ingest_portfolio_url(profile_id, url)` (modeled on `ingest_readme`, lines 126–199), and instantiate `self.web_parser = WebPageParser()` in the constructor (lines 30–53).
- **Edit:** `ingestion/chunking/strategy_selector.py` (lines 24–32) — add a `"web"` branch to `select_chunker(source_type)`, mapping to `StructuralChunker` (same rationale as `"readme"`).
- **Edit:** `api/routes/profiles.py` — `create_profile_endpoint` (lines 23–108) must call `pipeline.ingest_portfolio_url(profile_id, portfolio_url)` after `create_profile()` succeeds, when `portfolio_url` is provided. Likely also `update_profile_endpoint` (lines 147–193) if a user adds/changes their portfolio URL after initial creation.
- **Edit (maybe):** `pyproject.toml` (dependencies, ~lines 13–35) — add `beautifulsoup4` if regex-based HTML stripping proves too fragile for real portfolio sites.
- **New tests:** `tests/unit/test_web_page_parser.py` (mirroring `tests/unit/test_resume_parser.py`'s fixture/mock style), and `tests/unit/test_pipeline.py` covering `ingest_portfolio_url` (no existing pipeline test file today).
- **No changes expected:** `core/models/ingested_source.py` — `source_type` is a free-text column whose comment already lists `"web"` as an anticipated value, and `source_url` already exists (line 34) unused. `core/models/profile.py` / `api/schemas/profile.py` already carry `portfolio_url` end-to-end.

### Plan

1. Write `WebPageParser` (`ingestion/parsers/web_page_parser.py`): fetch the URL with `httpx` (reusing the timeout/error-handling pattern from `github_tool.py`), strip HTML to plain text, return a `ParseResult(text, metadata, source_type="web")` like the other parsers.
2. Add `IngestionPipeline.ingest_portfolio_url(profile_id, url)` in `ingestion/pipeline.py`: call the new parser, hash content (`_hash_content`), chunk via `StrategySelector`, embed via `BatchEmbeddingProcessor`, and store via `VectorStore.add_chunks` — following the exact structure of `ingest_readme`.
3. Add the `"web"` → `StructuralChunker` mapping in `ingestion/chunking/strategy_selector.py`.
4. Wire the API route: in `create_profile_endpoint` (and `update_profile_endpoint`), after the profile record is created/updated, call `pipeline.ingest_portfolio_url(profile.id, portfolio_url)` when `portfolio_url` is present. Decide sync vs. fire-and-forget based on how resume/readme ingestion end up being wired (currently neither is wired either — may be a broader, pre-existing gap worth flagging rather than silently fixing all three).
5. Write unit tests: `test_web_page_parser.py` (successful fetch, HTTP error, empty/malformed HTML) and `test_pipeline.py::test_ingest_portfolio_url` (happy path + skip-if-unchanged via `_check_skip`).

### Inputs & outputs

- **Input:** a `portfolio_url` string (already validated at the Pydantic layer as `Optional[str]`) tied to a `profile_id`.
- **Output:** a set of embedded chunks written to the Chroma vector store (via `VectorStore.add_chunks`) associated with that `profile_id`, retrievable later by the RAG retriever alongside resume/readme/repo chunks; and (once `_record_ingested_source` is implemented for real, rather than left as a stub) a row in `IngestedSource` with `source_type="web"`, `source_url=<the url>`, `content_hash`, and `chunk_count`.

### Risks & unknowns

- **`_check_skip()` and `_record_ingested_source()` are currently stubs** (`ingestion/pipeline.py` lines 280–308, 310–341) — they log but don't actually query/persist. Need to confirm whether completing these is in scope for this issue or should be flagged as a separate follow-up, since without them re-ingestion dedup won't really work for any source type, not just portfolio URLs.
- **No HTML parsing library is currently a dependency** — regex-based stripping (as `resume_parser.py` does for its own HTML cleanup) may produce noisy/low-quality text on real-world portfolio sites (nav bars, footers, scripts, JSON-LD blobs). Need to decide early whether to add `beautifulsoup4` or accept lower-quality extraction for v1.
- **No existing caller for `IngestionPipeline` at all** — resume/readme/repo ingestion aren't invoked from any route today either, only `scripts/seed_db.py` might call the pipeline directly. Wiring the portfolio-URL path into `api/routes/profiles.py` may surface this as a broader wiring gap larger than issue #11's stated scope.
- **Fetch reliability/security:** arbitrary user-supplied URLs raise SSRF-adjacent concerns (fetching internal/private addresses) and slow/hanging responses — need a sane timeout (matching `github_tool.py`'s `timeout=10.0`) and possibly URL validation before fetching.
- **Sync vs. async ingestion:** if `ingest_portfolio_url` runs synchronously inside the `create_profile_endpoint` request, a slow/unreachable portfolio site could stall profile creation. No background job infra (Celery, etc.) currently exists in the codebase, so this may need to be a "best-effort, don't fail profile creation" call rather than blocking.

### Edge cases

- `portfolio_url` is omitted or empty — skip ingestion entirely (no-op), same as today.
- URL is unreachable, times out, or returns a non-2xx status — log and continue without failing profile creation (mirror `github_tool.py`'s `httpx.HTTPStatusError` handling).
- URL returns non-HTML content (PDF, image, JSON) — detect via `Content-Type` header and skip/handle gracefully rather than attempting to strip HTML from binary data.
- Page has little or no extractable text (e.g. JS-rendered SPA with an empty initial HTML shell) — resulting chunk count could be zero; pipeline should handle "no chunks produced" without erroring.
- Re-ingesting the same unchanged URL — should be a no-op once `_check_skip()`'s content-hash comparison is implemented for real.
- Malformed/invalid URL string reaching the parser — validate and fail fast with a clear error rather than letting `httpx` raise an unhandled exception.
