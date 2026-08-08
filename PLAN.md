## Solution plan

**Issue:** Add support for ingesting a portfolio website URL (https://github.com/ascherj/pathreview/issues/11)

### Understand
**Root Cause/Gap:** The current ingestion pipeline only supports ingesting Resumes and GitHub READMEs/repo data. Users cannot provide a personal portfolio website as a data source, limiting the context the application has about the user.
**Expected Behavior:** The user should be able to provide a URL to their portfolio website. The backend should scrape/parse the text from the website, extract relevant information (bio, projects, skills), chunk the data, generate embeddings, and store them in the vector database just like the existing resume and README flows.
**Actual Behavior:** The feature does not exist yet.

### Map
Files involved:
- `ingestion/parsers/web_parser.py` (NEW): To fetch and extract text from the provided URL.
- `ingestion/pipeline.py` (MODIFY): Add an `ingest_portfolio` method inside `IngestionPipeline` to handle the parsing, chunking, and embedding.
- `api/schemas/profile.py` (MODIFY): Update the schema to allow a portfolio URL to be provided in the user's profile.

### Plan
1. **Create WebParser:** Implement a `WebParser` class in `ingestion/parsers/web_parser.py` (likely inheriting from a base parser) that takes a URL, fetches the HTML content, and extracts the text while stripping out boilerplate navigation and footers.
2. **Update Schema:** Modify `api/schemas/profile.py` to add a `portfolio_url` field to the profile input data models.
3. **Extend Pipeline:** Add `ingest_portfolio(self, profile_id: str, url: str) -> IngestResult` to `ingestion/pipeline.py`. This will call the `WebParser`, process the text, chunk it, and save the embeddings.
4. **Testing:** Test the pipeline locally by passing a sample portfolio URL to ensure it is fetched, parsed, and ingested correctly without errors.

### Inputs & outputs
**Inputs:** A string representing the portfolio website URL (e.g., `https://my-portfolio.com`), along with the user's `profile_id`.
**Outputs:** An `IngestResult` object indicating the success of the ingestion, the number of chunks created, and if it was skipped. Behind the scenes, the chunked text and its vector embeddings are stored in ChromaDB.

### Risks & unknowns
- **Scraping blockages:** The website might block automated requests or require JavaScript to render the content. (Unknown: Do we need a headless browser like Puppeteer/Selenium, or is simple HTTP GET via `requests` enough? Assuming HTTP GET for now).
- **Poor text extraction:** HTML might have poor semantics, making it hard to extract the actual bio/projects instead of navigation headers or scripts.

### Edge cases
- **Invalid URLs:** The URL might be malformed, or the site might return a 404/500 error. The `ingest_portfolio` method should catch these exceptions gracefully and return an appropriate failure or skip state.
- **Empty content:** The website might have very little text or just images.
- **Timeouts:** The request to the portfolio website might time out. This needs to be handled to avoid hanging the entire ingestion pipeline.
