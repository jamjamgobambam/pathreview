# Solution Plan

**Issue:** [API reference doc is missing the POST /profiles request body schema](https://github.com/ascherj/pathreview/issues/89)

## Understand

The root cause of this issue is that [docs/API.md](docs/API.md) only provides endpoint descriptions but lacks detailed request body schemas for POST endpoints. Specifically:

**Expected behavior:** The API documentation should include complete request body schemas with field names, data types, whether fields are required/optional, constraints (like max length), accepted file types, and example values for POST endpoints.

**Actual behavior:** The documentation only shows one-line descriptions like `POST /profiles — Create a profile with resume and GitHub username` without detailing the actual request structure.

This creates a poor developer experience because:
- Frontend developers don't know what fields to send
- They don't know which fields are required vs optional
- Data type information is missing (strings, UUIDs, files, etc.)
- Validation constraints (max lengths, file type restrictions) are unclear
- Example requests are not provided

The issue specifically mentions two endpoints:
1. `POST /profiles` - accepts multipart form data with github_username, portfolio_url, and resume_file
2. `POST /reviews` - accepts JSON body with profile_id

## Map

**Files involved:**

1. **[docs/API.md](docs/API.md)** (lines 16-26) — The main API reference documentation that needs updating
2. **[api/routes/profiles.py](api/routes/profiles.py)** (lines 23-30) — Implementation showing POST /profiles accepts Form fields and File upload
3. **[api/schemas/profile.py](api/schemas/profile.py)** (lines 7-10) — Pydantic schema defining ProfileCreate with field constraints
4. **[api/routes/reviews.py](api/routes/reviews.py)** (lines 22-28) — Implementation showing POST /reviews accepts ReviewCreate JSON body
5. **[api/schemas/review.py](api/schemas/review.py)** (lines 14-15) — Pydantic schema defining ReviewCreate with profile_id field

## Plan

### Step 1: Add POST /profiles request body schema
Edit [docs/API.md](docs/API.md) to add a detailed request body section under the `POST /profiles` endpoint that includes:
- Content-Type (multipart/form-data)
- All three form fields with types and constraints
- File type requirements for resume_file
- Example curl request

### Step 2: Add POST /reviews request body schema
Edit [docs/API.md](docs/API.md) to add a detailed request body section under the `POST /reviews` endpoint that includes:
- Content-Type (application/json)
- The profile_id field with UUID type
- Example JSON payload
- Example curl request

### Step 3: Add response schema examples (stretch)
If time permits, also document the response schemas (ProfileResponse, ReviewResponse) to provide a complete reference.

### Step 4: Remove reproduction HTML comments
Clean up the HTML comment blocks added during reproduction.

### Step 5: Verify documentation accuracy
Cross-reference the added documentation with the actual endpoint implementations to ensure accuracy.

## Inputs & outputs

**Inputs:**
- Existing endpoint implementations in [api/routes/profiles.py](api/routes/profiles.py) and [api/routes/reviews.py](api/routes/reviews.py)
- Pydantic schemas in [api/schemas/profile.py](api/schemas/profile.py) and [api/schemas/review.py](api/schemas/review.py)
- Current [docs/API.md](docs/API.md) structure and formatting

**Outputs:**
- Updated [docs/API.md](docs/API.md) with complete request body schemas for both POST endpoints
- Clear field descriptions including types, constraints, and requirements
- Example requests showing proper usage
- Documentation that matches the actual API implementation

## Risks & unknowns

**Risks:**
1. **Inconsistency with implementation:** The documentation must accurately reflect the actual API behavior. If I misinterpret the code, the docs will mislead developers.
   - Mitigation: Carefully read both the route handlers and Pydantic schemas; test locally if needed

2. **Format/style mismatch:** The API.md file may have an established formatting style I should follow.
   - Mitigation: Study the existing format and maintain consistency

3. **Incomplete coverage:** The issue mentions POST endpoints but there might be other endpoints with missing schemas.
   - Mitigation: Focus on the two mentioned endpoints (POST /profiles and POST /reviews) as specified in the issue

**Unknowns:**
1. Should I document all optional authentication headers (JWT tokens)?
2. Should response schemas also be added, or just request schemas?
3. Are there any existing documentation standards or templates in the codebase?

## Edge cases

**Input validation edge cases to document:**
1. **POST /profiles:**
   - What happens if resume_file is provided but not PDF/Markdown? (Returns 422)
   - What happens if PDF parsing fails? (Returns 422)
   - Can both github_username and portfolio_url be omitted? (Yes, both are optional)
   - What's the maximum file size for resume_file? (Not specified in code, may need to note)

2. **POST /reviews:**
   - What happens if profile_id doesn't exist or doesn't belong to the user? (Likely 404, should verify)
   - What happens if profile_id is malformed (not a valid UUID)? (422 validation error)

**Documentation edge cases:**
1. Ensure field descriptions are clear about optional vs required
2. Note authentication requirements (both endpoints require JWT token)
3. Clarify the multipart/form-data encoding for file uploads
4. Provide realistic UUID examples (not placeholder text)
