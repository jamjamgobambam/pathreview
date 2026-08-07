# Solution Plan

**Issue:** Add support for ingesting a portfolio website URL  
https://github.com/ascherj/pathreview/issues/11

## Understand

PathReview currently allows users to submit a portfolio URL through the profile form and stores that value in the database. However, the application does not currently retrieve or analyze the content from the provided website. The review pipeline only references the portfolio URL instead of extracting useful information from the webpage.

The expected behavior is that when a user provides a portfolio URL, PathReview should fetch the website content, extract relevant information such as project descriptions, skills, and biography details, and include this information alongside existing sources like GitHub repositories and resumes during AI-generated reviews.

## Map

The following files and modules are involved in supporting portfolio URL ingestion:

- `api/routes/profiles.py`
  - Receives portfolio URL input from the user through the profile submission endpoint.

- `api/schemas/profile.py`
  - Validates the portfolio URL field and defines the expected profile data structure.

- `core/models/profile.py`
  - Stores portfolio URL information in the database profile model.

- `core/services/profile_service.py`
  - Handles saving and updating profile information, including the portfolio URL.

- `core/services/review_service.py`
  - Currently references portfolio URLs during review generation but does not ingest or extract webpage content.

- `ingestion/parsers/`
  - Contains existing document parsers for sources such as resumes and README files. A new parser for portfolio webpage content will likely be added here.

- `ingestion/pipeline.py`
  - Coordinates document ingestion, parsing, chunking, and embedding. Portfolio ingestion will need to be integrated into this workflow.

## Plan

1. Create a portfolio webpage parser that accepts a portfolio URL, retrieves webpage content, and extracts readable text and relevant metadata.

2. Add validation and error handling for invalid URLs, unavailable websites, empty pages, or failed content extraction.

3. Integrate portfolio URL ingestion into the existing ingestion pipeline so portfolio content follows the same processing flow as resumes and README files.

4. Convert extracted portfolio content into chunks and generate embeddings so the information can be stored in the vector database.

5. Verify that portfolio information is included with existing profile sources and improves AI-generated review results.

## Inputs & Outputs

**Input:**
- A user-provided portfolio website URL submitted through the profile form.

**Output:**
- Extracted webpage text and metadata from the portfolio website.
- Portfolio content stored as embeddings in the vector database.
- Portfolio information available as a source during AI-generated reviews.

## Risks & Unknowns

- Need to determine the most appropriate webpage extraction approach or library for this project.
- Portfolio websites may have different layouts and HTML structures, making extraction inconsistent.
- Some websites may block automated requests or require JavaScript rendering.
- Need to confirm how portfolio ingestion should be tracked in the existing `ingested_sources` database workflow.
- Need to ensure large webpages do not create excessive ingestion or embedding costs.

## Edge Cases

- Invalid portfolio URL format.
- Website is unavailable or returns an error response.
- Portfolio page contains little or no readable text.
- Portfolio website has very large amounts of content.
- Portfolio pages require JavaScript rendering to display content.
- Website content changes after previous ingestion.