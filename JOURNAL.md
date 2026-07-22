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