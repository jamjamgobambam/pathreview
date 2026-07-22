## Solution plan

**Issue:** [Add support for ingesting a portfolio website URL](https://github.com/ascherj/pathreview/issues/11)

### Understand
The `portfolio_url` field exists end-to-end (DB column, Pydantic schema, frontend form), so a user can submit one today, but nothing ever fetches it. The root cause is that `core/services/review_service.py`'s `_run_ingestion_pipeline` fabricates a placeholder string (`f"Portfolio data from {url}"`) instead of calling a real parser, and `ingestion/pipeline.py` has no `ingest_portfolio` method or corresponding `web_parser.py` to call in the first place — unlike resumes/READMEs/repos, which all go through real parse → chunk → embed steps. Expected behavior: submitting a portfolio URL should result in the page's actual text (bio, project descriptions) being fetched, parsed, chunked, embedded, and stored so it's retrievable during a review, the same way README/resume content is. Actual behavior: the review always uses a fake, content-free string regardless of what's really on the page, so the review's output is never actually informed by the portfolio site (confirmed in Week 8 repro: fake server access log stayed empty across a full review run).

### Map
- `ingestion/parsers/web_parser.py` (new) — fetch + extract text from a URL, subclass `BaseParser`, return `ParseResult(text, metadata, source_type="portfolio")` per the contract in `ingestion/parsers/base.py`.
- `ingestion/pipeline.py` — add `IngestionPipeline.ingest_portfolio(profile_id, url)`, mirroring `ingest_readme`/`ingest_resume` (dedup via `_check_skip`/`_hash_content`, chunk via `StrategySelector`, embed via `BatchEmbeddingProcessor`, record via `_record_ingested_source`).
- `core/services/review_service.py` — replace the placeholder block (`_run_ingestion_pipeline`, portfolio branch) with a real call into `IngestionPipeline.ingest_portfolio`, since this is the actual trigger point today (not the currently-unwired `ingestion/pipeline.py` class).
- `api/schemas/profile.py` — `portfolio_url` already exists on `ProfileCreate`/`ProfileUpdate`; likely just needs a stricter validator (real URL format, not just `max_length=500`) rather than a new field.
- `pyproject.toml` — `httpx` is already a dependency (used elsewhere), so it can serve as the HTTP client, but there's no HTML-parsing library yet (no bs4/lxml); need to add one or rely on `html.parser`/regex for a minimal implementation.
- `tests/unit/test_web_parser.py` (new) — following the pattern in `tests/unit/test_readme_parser.py`.

### Plan
1. Write `web_parser.py`: fetch the URL with `httpx` (timeout + basic error handling for unreachable/non-200 responses), strip HTML to plain text, and return a `ParseResult` with metadata like `word_count`/`title` similar to `readme_parser.py`'s shape.
2. Add `ingest_portfolio` to `IngestionPipeline`, copying the `ingest_readme` structure (parse → metadata → chunk → embed → record), using `source_id = f"portfolio_{profile_id}_{hash(url)}"`.
3. Wire `review_service.py`'s portfolio branch to call `ingest_portfolio` instead of building the placeholder dict, keeping the existing `IngestedSource` recording behavior but backed by real fetched content.
4. Tighten `portfolio_url` validation in `api/schemas/profile.py` (e.g. Pydantic `HttpUrl` or a custom validator) so obviously malformed URLs are rejected before they ever reach ingestion.
5. Add unit tests for `web_parser.py` (parse success, malformed HTML, non-200/unreachable URL) and at least one test exercising `ingest_portfolio` on the pipeline, following existing test conventions.

### Inputs & outputs
- Input: a `profile_id` and a `portfolio_url` string (already validated/stored on the `Profile` row).
- Output: an embedded, chunked representation of the portfolio page's text stored in the vector DB and an `IngestedSource` row with `source_type="portfolio"` containing real extracted text (not a placeholder), retrievable during review generation the same way resume/README content is.

### Risks & unknowns
- No HTML-parsing dependency exists yet — need to decide whether to add `beautifulsoup4` (or similar) or hand-roll minimal stripping with stdlib `html.parser`; adding a new dependency is a small scope increase worth calling out in the PR.
- Portfolio sites vary wildly (SPA/JS-rendered pages, marketing sites, blogs) — a plain HTTP fetch won't get content that's client-side rendered; need to explicitly scope this to static/server-rendered HTML and note the limitation rather than trying to solve JS rendering.
- Network calls introduce failure modes (timeouts, 404s, redirects, non-HTML content-type) that the existing parsers don't have to handle at all — need sensible fallback behavior (e.g. skip ingestion and log, don't fail the whole review) matching the `try/except` pattern already used around the portfolio block in `review_service.py`.
- `ingestion/pipeline.py` is currently dead code (not imported anywhere) — need to confirm during implementation whether the intended fix is to wire it into `review_service.py` (as planned above) or whether this pipeline class is meant to be replaced/consolidated with the logic already in `review_service.py`. Worth a quick check-in on this before or during implementation.

### Edge cases
- Portfolio URL unreachable, times out, or returns non-200 — should log and skip gracefully, not crash the review.
- URL returns non-HTML content (PDF, image, JSON) — should be detected via content-type and skipped rather than mis-parsed as text.
- Extremely large pages — should not be embedded unbounded; reuse whatever size/chunking limits the existing `StrategySelector` already applies to READMEs.
- Empty/near-empty page (e.g. JS-only shell with no server-rendered content) — should produce a low-signal but non-crashing result, and this limitation should be documented rather than silently treated as success.
- Same portfolio URL submitted twice for the same profile — should be deduplicated via `_check_skip`, same as other source types.