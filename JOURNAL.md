## Week 7 — Issue selection

***Issue link:*** https://github.com/ascherj/pathreview/issues/89
***Issue title:*** API reference doc is missing the POST /profiles request body schema
***Tier:*** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

***Problem summary:***
The current API reference documentation does not include the expected request body schema for the `POST /profiles` endpoint. This makes it difficult for developers or frontend services to know exactly what parameters and data types are required when creating a user profile. A successful fix will involve updating the API documentation (likely under the `api/` or `docs/` module) to accurately reflect the Pydantic model or schema utilized by the FastAPI router for profile ingestion.

***Branch name:*** docs/89-post-profiles-schema
***Setup confirmation:*** [x] App runs locally at localhost:5173
***Cohort ledger:*** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/abishektony/pathreview/commit/dbd81d389dcf329c7dac05ace2a749901c736eb2

**Reproduction summary:**
I reproduced the issue by comparing [docs/API.md](docs/API.md) with the actual endpoint implementations in [api/routes/profiles.py](api/routes/profiles.py) and [api/routes/reviews.py](api/routes/reviews.py). The documentation only provides one-line endpoint descriptions without request body schemas. I added HTML comments in the docs file documenting exactly what's missing: POST /profiles needs multipart form data schema (github_username, portfolio_url, resume_file), and POST /reviews needs JSON body schema (profile_id).

**PLAN.md link:** https://github.com/abishektony/pathreview/blob/docs/89-post-profiles-schema/PLAN.md

**Walkthrough video (recommended):** [Will record if needed for feedback]

**Blockers or open questions:**
None at this time. The reproduction is clear and the solution approach is straightforward - add detailed request body schemas to the API documentation based on the Pydantic models and route handler signatures.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have completed the core implementation of the fix. Both POST endpoints now have comprehensive request body schemas in docs/API.md:

✅ **Step 1 complete:** Added POST /profiles schema with multipart/form-data format, all three fields (github_username, portfolio_url, resume_file), validation rules, and example curl request
✅ **Step 2 complete:** Added POST /reviews schema with JSON format, profile_id field (UUID), error responses, and example curl request
✅ **Step 5 complete:** Verified all documentation against source code (api/routes/profiles.py, api/routes/reviews.py, and Pydantic schemas) - everything is accurate

The documentation now includes:
- Content-Type specifications
- Field tables with types, requirements, and descriptions
- Validation rules and constraints
- Example curl requests with proper headers
- Example response JSON
- Error response documentation

**Next steps:**
- Review CONTRIBUTING.md for any documentation-specific conventions
- Add Week 9 Check-in 2 after final review
- Prepare and open draft PR for feedback
- Update JOURNAL.md with PR link

**Blockers:**
None. The fix is complete and ready for review. Note: make check and make test-unit cannot run in this environment (no .venv setup), but this is a documentation-only change with no code modifications, so no tests are needed.