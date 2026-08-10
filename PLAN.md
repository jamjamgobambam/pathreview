## Solution plan

**Issue:** Add support for ingesting a portfolio website URL — https://github.com/ascherj/pathreview/issues/11

### Understand
Before this fix, `_run_ingestion_pipeline()` in `core/services/review_service.py` treated `profile.portfolio_url` as metadata only: it wrote a hardcoded placeholder string (`f"Portfolio data from {profile.portfolio_url}"`) into `IngestedSource` instead of fetching the page. Expected behavior: a portfolio URL should be fetched over HTTP, have its visible text extracted (skipping `<script>`/`<style>`/`<noscript>`), and that real text should flow into `ingestion_results` so downstream RAG/agent steps have actual evidence to work with. Actual (pre-fix) behavior: portfolio content never left the placeholder string, so review generation could never reference anything a candidate actually put on their site.

Root cause: no HTML-fetching/parsing implementation existed for the `web` source type — `ingestion/parsers/web_parser.py` didn't exist yet, and `_run_ingestion_pipeline` never called out to a parser for the portfolio branch.

### Map
- `ingestion/parsers/web_parser.py` — new `WebParser` class: fetches URL via `httpx.get`, extracts visible text + title via a custom `HTMLParser` subclass, computes `content_hash`, returns a `ParseResult`.
- `ingestion/parsers/base.py` — existing `BaseParser`/`ParseResult` contract `WebParser` implements (no changes needed, confirmed shape).
- `core/services/review_service.py` — `_run_ingestion_pipeline()` portfolio branch: replace placeholder string with `WebParser().parse(profile.portfolio_url)`; also aligned `IngestedSource` fields (`source_type="web"`, `source_url`, `content_hash`) across all three branches (github/portfolio/resume) for consistency.
- `tests/unit/test_web_parser.py` — new unit tests for `WebParser` (visible-text extraction, title fallback, bytes input, invalid URL, HTTP error propagation).
- `tests/unit/test_review_service.py` — updated tests asserting the ingestion pipeline calls `WebParser` and stores real extracted text/hash for the portfolio source.

### Plan
1. Implement `_VisibleTextExtractor(HTMLParser)` to strip script/style/noscript content and separately capture `<title>` text.
2. Implement `WebParser.parse()`: validate input is an http(s) URL string/bytes, fetch with `httpx.get(follow_redirects=True, timeout=10.0)`, raise on non-2xx via `raise_for_status()`, extract text/title, compute `content_hash` (sha256) and `word_count`.
3. Wire `WebParser` into `_run_ingestion_pipeline`'s portfolio branch in `review_service.py`, replacing the placeholder and populating `IngestedSource` with real `source_url`/`content_hash`.
4. Add/extend unit tests (mocking `httpx.get`) covering happy path, bytes input, invalid URL, non-HTTP scheme, and HTTP error propagation.
5. Manually smoke-test against a local fixture (`tmp/portfolio_site/index.html` served locally) to confirm the parser round-trips against a real HTTP response, not just mocks.

### Inputs & outputs
- **Input:** `profile.portfolio_url` (string, expected `http://`/`https://`), or raw HTML fetched from that URL.
- **Output:** `ParseResult(text, metadata, source_type="web")` where `metadata` contains `source_type`, `url`, `title`, `word_count`, `content_hash`. Downstream, this produces a persisted `IngestedSource` row with real `source_url`/`content_hash` and a `portfolio_data["data"]` entry containing actual page text for the agent/RAG steps.

### Risks & unknowns
- **JS-rendered portfolios (SPAs):** `httpx.get` only returns server-rendered HTML — sites that render content client-side (React/Vue portfolios with an empty `<div id="root">`) will yield near-empty extracted text. The local fixture in `tmp/portfolio_site/index.html` is static HTML and doesn't exercise this case; needs a follow-up decision (headless rendering vs. documented limitation).
- **Timeouts/unreachable hosts:** fixed 10s timeout in `web_parser.py:83` — unclear if that's sufficient for slow portfolio hosts, and `_run_ingestion_pipeline`'s `except Exception` swallows the error into a log line, so a slow/broken portfolio silently drops that source rather than surfacing to the user.
- **Non-UTF-8 or non-HTML responses:** if a portfolio URL points at a PDF or non-UTF-8 page, `response.text` decoding and `HTMLParser.feed()` behavior is unverified.
- **Redirect loops / SSRF-style URLs:** `follow_redirects=True` with no allowlist means the portfolio URL could redirect to an internal address; not currently addressed.

### Edge cases
- Non-http(s) scheme (`ftp://`, bare domain with no scheme) → `ValueError` (covered by `test_parse_invalid_url_raises_value_error`).
- Non-string, non-bytes `content` (e.g. `None`, `int`) → `ValueError` (covered by `test_parse_non_string_content_raises_value_error`).
- HTTP error status (4xx/5xx) → propagates `httpx.HTTPStatusError` (covered by `test_http_error_propagates`).
- Missing `<title>` tag → falls back to `_extract_title_fallback`, and if that also finds nothing, `title` is `""`.
- Page with only `<script>`/`<style>` content and no visible text → `page_text` is `""`, `word_count` is `0`, still returns a valid `ParseResult` rather than raising.
- Bytes-encoded URL input → decoded via `content.decode("utf-8", errors="replace")` (covered by `test_parse_accepts_bytes_url`).
