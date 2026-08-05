# Solution plan

**Issue:** [Implement a caching layer for repeated identical portfolio queries (#32)](https://github.com/ascherj/pathreview/issues/32)

## Understand

Currently, the application regenerates a portfolio review every time a user submits a review request, even when the portfolio content has not changed. The review service always executes the ingestion pipeline, agent orchestration, retrieval, and review generation regardless of whether an identical review already exists. The expected behavior is to detect unchanged portfolio content using a content hash and reuse a previously completed review instead of rerunning the full pipeline.

## Map

### Files involved

- `core/services/review_service.py`

  - `process_review()`
  - `_run_ingestion_pipeline()`
  - `_run_rag_retrieval_generation()`

- `rag/generator/review_generator.py`

  - `generate_full_review()`

- `core/models/review.py` (if a content hash field needs to be added)

### Components involved

- Review processing workflow
- Database review storage
- RAG retrieval and generation pipeline
- Portfolio ingestion pipeline

## Plan

1. Investigate the current review workflow to determine where a cache lookup should occur before the ingestion pipeline begins.
2. Create a deterministic hash based on the portfolio content (such as the GitHub username, portfolio URL, resume text, and any other fields that influence review generation).
3. Search for an existing completed review associated with the same content hash.
4. If a matching review exists, reuse its sections and overall score instead of executing ingestion, retrieval, and generation.
5. If no cached review exists, continue the normal review pipeline and store the generated review together with its content hash for future requests.

## Inputs & outputs

### Inputs

- GitHub username
- Resume PDF
- Portfolio URL

### Outputs

If a cached review exists:

- Return the previously generated review.
- Skip ingestion.
- Skip retrieval.
- Skip review generation.

If no cached review exists:

- Run the existing review pipeline.
- Save the completed review.
- Store the computed content hash for future cache lookups.

## Risks & unknowns

- The `Review` model may not currently contain a field for storing a content hash, requiring a database migration.
- Determining which profile fields should be included when generating the hash.
- Ensuring the hashing process is deterministic so that identical portfolio content always produces the same hash.
- Avoiding false cache hits when any relevant portfolio information has changed.

## Edge cases

- A user updates their resume but leaves the GitHub username unchanged.
- A user updates their portfolio URL after receiving a review.
- Profiles with invalid GitHub usernames or portfolio URLs.
- Empty or missing resume PDF.
- Reviews with a status of `pending` or `failed` should not be reused.
- Multiple users submitting identical portfolio content should still produce the expected caching behavior according to the project's design.
