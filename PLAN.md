# Solution Plan

**Issue:** Add end-to-end ingestion test with a sample resume fixture

**Issue Link:** https://github.com/ascheri/pathreview/issues/18

---

## Understand

The project currently has unit tests for individual resume parsers, but it does not have an integration test that verifies the complete ingestion workflow. This means there is no automated test confirming that a resume can be uploaded, processed, embedded, and stored successfully from beginning to end. The goal of this issue is to create an end-to-end integration test using the provided sample resume fixtures so the entire ingestion pipeline is verified automatically.

---

## Map

### Files likely to be involved

- `tests/integration/test_ingestion_pipeline.py`
- `tests/fixtures/sample_resumes/`
- `ingestion/`
- Any helper utilities used by the ingestion pipeline
- Existing integration test fixtures and configuration

These files will be inspected to understand how the ingestion pipeline works, how sample resumes are loaded, and how current integration tests are structured.

---

## Plan

1. Read `tests/integration/test_ingestion_pipeline.py` to understand the current integration test structure.
2. Examine the sample resume fixtures inside `tests/fixtures/sample_resumes/` and determine how they are used.
3. Trace the resume ingestion workflow from file upload through processing and storage.
4. Add a new end-to-end integration test that exercises the complete ingestion pipeline using one of the provided sample resumes.
5. Run the integration test suite, verify the new test passes, and confirm that no existing tests fail.

---

## Inputs & Outputs

### Inputs

- A sample resume fixture from `tests/fixtures/sample_resumes/`
- The ingestion pipeline
- Database and supporting services started through Docker

### Expected Outputs

- A new integration test that covers the complete resume ingestion workflow.
- Verification that the resume is processed successfully.
- Confirmation that the expected data is stored or returned after ingestion.
- A passing integration test that helps prevent future regressions.

---

## Risks & Unknowns

- The ingestion pipeline may depend on database state or services that require additional setup.
- Existing helper functions or fixtures may need to be reused instead of creating new ones.
- The current integration test framework may require specific setup or cleanup procedures.
- Additional modules may be involved after tracing the ingestion pipeline.
- The expected output format may require further investigation before assertions can be written.

---

## Edge Cases

1. The sample resume is missing required fields.
2. The uploaded resume file is malformed or unsupported.
3. The ingestion pipeline encounters an unexpected processing error.
4. Duplicate resume uploads should be handled consistently.
5. The pipeline should not partially save incomplete or invalid data if processing fails.