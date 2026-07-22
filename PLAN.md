## Solution plan

**Issue:** Add support for ingesting a portfolio website URL — https://github.com/ascherj/pathreview/issues/11

### Understand

Users can already type their portfolio website URL into PathReview and it gets saved, but the app never actually visits the site. The feature was scaffolded and then left unfinished. When a review runs, the code in core/services/review_service.py (around lines 229–252) just builds a hard-coded string, `f"Portfolio data from {profile.portfolio_url}"`, and stores that instead of the real page. So the URL is captured but the content behind it is never fetched.

What should happen is that when someone submits a URL like https://janedoe.dev, PathReview downloads the page, pulls out the readable text such as their bio and project descriptions, and adds that text to the vector store, which is the same place resume and README content already goes. That way the AI reviewer can point to what's actually written on the portfolio. What happens right now is that the only "portfolio content" the AI ever sees is that placeholder string, so nothing real from the site is ever used.

The root cause is just that three pieces were never built: there's no parser that knows how to read a web page, there's no ingest_portfolio method in the pipeline, and the review service still uses the placeholder instead of calling real ingestion.

### Map

The three existing source types (resume, README, repo) all follow the same shape, so I'm going to copy that shape. Each one has a parser in ingestion/parsers/ that turns raw input into clean text plus some metadata, and each one has a matching method in ingestion/pipeline.py that chunks the text, embeds it, and stores it. A portfolio website is just a fourth source that fits the same pattern.

One thing that makes this easier is that the front half already works. The URL travels from the form in frontend/src/components/ProfileForm.tsx, through the API in api/routes/profiles.py and api/schemas/profile.py, and into the database in core/services/profile_service.py (the column itself is defined in alembic/versions/001_initial_schema.py). So I don't need to touch any of that plumbing, only the part that fetches and processes the page.

Files I expect to touch:

- ingestion/parsers/web_parser.py (new) — the class that fetches a URL and extracts readable text.
- ingestion/pipeline.py — add an ingest_portfolio method and register the new parser.
- api/schemas/profile.py — confirm the portfolio_url field is there and add light validation if needed.
- pyproject.toml — add a library for pulling text out of HTML.
- tests/unit/ — add tests for the parser and the new pipeline method.
- core/services/review_service.py — possibly, to replace the placeholder (see risks about scope).

### Plan

1. Add an HTML-parsing dependency to pyproject.toml. httpx is already installed and handles downloading the page, but there's no library yet for extracting readable text out of the HTML, so I'll add one (probably beautifulsoup4, or trafilatura if it gives cleaner results).

2. Create ingestion/parsers/web_parser.py with a WebParser class that extends BaseParser. Its parse method downloads the page with a timeout, follows redirects, strips out the noise like scripts, styles, nav, and footer, and returns a ParseResult with the readable text and some metadata (final URL, page title, word count).

3. Add an ingest_portfolio method to ingestion/pipeline.py that mirrors ingest_readme almost line for line: build a source_id, skip if it's already been ingested, call the parser, chunk the text, embed and store it, then record it. I'll also register a WebParser in the constructor next to the other parsers.

4. Confirm api/schemas/profile.py accepts portfolio_url (it already does) and add a simple check that the value looks like an http or https URL so bad input fails early.

5. Write tests for both pieces: feed the parser fixed sample HTML and check that the right text comes out and the noise is dropped, and test that ingest_portfolio produces chunks and records the source the way the other methods do.

### Inputs & outputs

The input is a portfolio website URL as a string, along with the profile id it belongs to. The output is that the readable text from that page gets chunked, embedded, and stored in the vector store, and an IngestedSource record is created, returned as an IngestResult just like the other ingest methods. The end result is that real portfolio text, instead of the placeholder string, becomes available to the AI reviewer as evidence.

### Risks & unknowns

The biggest unknown is scope. The placeholder that actually runs during a review is in core/services/review_service.py, which the issue doesn't list, and that function doesn't call the IngestionPipeline class at all (GitHub and resume are placeholders there too). So "done" could mean just adding ingest_portfolio to the pipeline, or it could mean also wiring the review service to use it so the feature works end to end. I'll build the pipeline method as the issue describes and check in Slack about whether the wiring is expected too.

Another risk is that some portfolios are JavaScript-heavy single-page apps that return almost no text unless a real browser runs them. Plain fetching can't render those, so I'll extract whatever is available and fail cleanly when there isn't anything, rather than pulling in a headless browser.

Fetching arbitrary user-supplied URLs is also security-sensitive, since a URL could point at an internal address, a huge page, or a redirect loop. I'll add a timeout, a size limit, and a content-type check. This project has a safety layer, so reviewers may care about this. And finally, adding a new dependency needs to fit the project's existing conventions and lockfiles.

### Edge cases

- The URL is unreachable, times out, or returns an error status like 404 or 500 — raise a clear error instead of crashing the review.
- The response isn't HTML (a PDF, image, or JSON) — reject it with a clear message.
- The page loads but has little or no readable text, like a JS-only site — handle it gracefully and record that nothing usable was found.
- The URL redirects — follow it but cap how many redirects, and store the final URL in metadata.
- The page is very large — enforce a size limit so ingestion stays fast.
- The same URL is submitted twice — the existing "skip if already ingested" check should stop duplicate work.
