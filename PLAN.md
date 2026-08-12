## Solution plan

**Issue:** [Add support for ingesting a portfolio website URL](https://github.com/ascherj/pathreview/issues/11)

### Understand
The project currently allows a user to provide a portfolio website URL, but the application does not process the website’s contents as part of the ingestion pipeline.

The profile schema already includes a `portfolio_url` field, so the URL can be accepted and stored. However, the ingestion system only supports resumes, GitHub README files, and repository metadata. There is no parser responsible for fetching and extracting text from a portfolio website and there is no pipeline method that sends portfolio content to the vector store.

#### Expected behavior

When a user provides a valid portfolio URL, PathReview should:

1. Fetch the webpage.
2. Extract useful, human-readable text from the page.
3. Convert the extracted content into documents or chunks compatible with the existing ingestion pipeline.
4. Store the content in the vector store so it can be used during portfolio analysis and review.

#### Actual behavior

The `portfolio_url` value is accepted by the profile schema, but it is not passed through an ingestion workflow. As a result, the portfolio website does not contribute any context to the generated review.

### Map
The following files and modules are involved:

- `ingestion/parsers/web_parser.py`
  - New parser for fetching a portfolio URL and extracting readable webpage content

- `ingestion/pipeline.py`
  - Initialize the new web parser
  - Add a method such as `ingest_portfolio()` to process and store portfolio website content.

- `api/schemas/profile.py`
  - Confirm that the existing `portfolio_url` field has the validation needed by the ingestion flow.
  - Update the schema only if additional URL validation or typing is necessary

- Existing parser modules in `ingestion/parsers/`
  - Use the resume and README parsers as references for return types, metadata, error handling, and code structure

- Existing ingestion tests
  - Add tests for webpage parsing and pipeline integration in the test location that matches the repository’s current testing structure.

### Plan

1. **Study the existing parser interface**
   - Review the resume and README parsers to determine the expected document structure, metadata fields, and error-handling conventions.
   - Confirm how parsed documents are passed into the vector store.

2. **Implement the web parser**
   - Create `ingestion/parsers/web_parser.py`.
   - Fetch the provided URL with a timeout
   - Parse the returned HTML
   - Remove non-content elements such as scripts, styles, etc where practical.
   - Return cleaned page text in the same document format used by the existing ingestion pipeline

3. **Add portfolio ingestion to the pipeline**
   - Initialize the web parser inside `IngestionPipeline`
   - Add an `ingest_portfolio()` method
   - Attach metadata identifying the source as a portfolio website and preserving the original URL
   - Pass the parsed content into the existing chunking, embedding, and storage workflow

4. **Connect the portfolio URL to the existing profile workflow**
   - Trace where resume and GitHub ingestion are triggered
   - Call the new portfolio ingestion method when a profile contains a non-empty `portfolio_url`.
   - Ensure profiles without a portfolio URL continue to work unchanged

5. **Add tests and verify behavior**
   - Test successful HTML extraction.
   - Test invalid URLs, connection failures, timeouts, empty pages, and unsupported responses.
   - Mock network requests so tests don't depend on live websites
   - Confirm portfolio content reaches the vector store with the expected metadata.


### Inputs & outputs
#### Input

The feature takes a portfolio website URL, for example:

```text
https://example.com
```

#### Output

The feature should produce one or more documents containing cleaned text extracted from the portfolio website.

Each document should include metadata consistent with the existing ingestion system, potentially including:

```text
{
    "source": "portfolio",
    "url": "https://example.com"
}
```

If the URL cannot be processed, the system should return or record a clear error without crashing unrelated ingestion tasks.

### Risks & unknowns
- The repository may already have a shared document format or parser base class that the new parser must follow.
- It's not yet clear where the complete profile-ingestion workflow is triggered, so an additional API, service, or task file may need to be modified
- Portfolio websites may depend heavily on JavaScript, while a standard HTTP request will only retrieve the initial HTML.
- Some sites may block automated requests or return rate-limit responses.
- Navigation menus, headers, repeated layout text, etc may reduce the quality of the extracted content.
- The project may expect ingestion failures to raise exceptions, return empty results, or be logged and skipped. This should match existing conventions.

### Edge cases
My feature should handle gracefully:
- Missing or empty portfolio URL; invalid URL format
- Unsupported URL schemes such as file://
- DNS failures or refused connections / request timeouts
- Redirects
- HTTP error responses such as 404, 403, or 500.
- Non-HTML responses such as PDFs or image files
- Pages with no meaningful visible text / containing only JavaScript-rendered content
- Duplicate ingestion of the same portfolio URL
- HTML containing scripts, styles, tracking text, or malformed markup
- Portfolio ingestion failing while resume or GitHub ingestion succeeds