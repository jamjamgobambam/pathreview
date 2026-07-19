## Week 7 — Issue selection

***Issue link:*** https://github.com/ascherj/pathreview/issues/89
***Issue title:*** API reference doc is missing the POST /profiles request body schema
***Tier:*** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

***Problem summary:*** 
The current API reference documentation does not include the expected request body schema for the `POST /profiles` endpoint. This makes it difficult for developers or frontend services to know exactly what parameters and data types are required when creating a user profile. A successful fix will involve updating the API documentation (likely under the `api/` or `docs/` module) to accurately reflect the Pydantic model or schema utilized by the FastAPI router for profile ingestion.

***Branch name:*** docs/89-post-profiles-schema
***Setup confirmation:*** [x] App runs locally at localhost:5173
***Cohort ledger:*** [x] Issue added to cohort ledger