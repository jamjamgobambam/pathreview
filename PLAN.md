## Solution plan

**Issue:** #89: API reference doc is missing the POST /profiles and POST /reviews request body schema (https://github.com/aschzerj/pathreview/issues/89)

### Understand
There is no root cause bug here, the gap is that docs/API.md lists both endpoints with only a route and a one line description, no request body schema. Expected behavior is that a contributor or API consumer can read API.md and know exactly what to send. Actual behavior is that they have to go read the FastAPI route code and Pydantic schemas themselves to figure it out.

### Map
- docs/API.md, the file I am actually editing
- api/routes/profiles.py, defines POST /profiles as multipart form data with github_username, portfolio_url, and an optional resume_file restricted to PDF, Markdown, or plain text, returns 422 on bad file type
- api/schemas/profile.py, the ProfileCreate model backing that form data
- api/routes/reviews.py, defines POST /reviews taking a JSON body with just profile_id, returns the review immediately with status "pending" while processing runs in the background
- api/schemas/review.py, the ReviewCreate model backing that JSON body

### Plan
1. Read through profiles.py and profile.py again to confirm field names, types, and required/optional status
2. Read through reviews.py and review.py the same way
3. Write a documented request schema for POST /profiles in API.md, including the multipart form fields and file type restriction, with an example
4. Write a documented request schema for POST /reviews in API.md, including the JSON body and pending status behavior, with an example
5. Start the app locally and compare both against the Swagger UI at localhost:8000/docs to confirm accuracy

### Inputs & outputs
Input is the existing route and schema code I already read. Output is an updated docs/API.md with field names, types, required vs optional status, and an example payload added under both POST /profiles and POST /reviews.

### Risks & unknowns
POST /profiles takes form data, not JSON, so I need to document the multipart format correctly rather than showing a plain JSON example. I am still not fully sure how much detail to include about the background processing behavior on POST /reviews since that is really review_service.py logic, not part of the request schema itself.

### Edge cases
Documenting what happens when resume_file is omitted, when it is an unsupported file type, and that github_username and portfolio_url are both optional on profile creation.