## Solution plan

**Issue:** 
https://github.com/ascherj/pathreview/issues/117
API docs don't include example curl commands #117

### Understand
docs/API.md just lists method + path + a one-line description for every endpoint, no curl examples or sample responses anywhere. So devs can't copy-paste anything to test the API, they'd have to go read the route code or open the UI instead. Fix is just adding curl examples to the doc.

### Map
Only file that needs changing is docs/API.md. Looked at the route files to see what the actual requests/responses look like: api/routes/health.py, auth.py, profiles.py, reviews.py. Nothing in the actual code needs to change.

### Plan
- add a curl command under each endpoint with the right headers/body
- add a sample response under each one too
- note that /auth/login uses form data not JSON, and POST /profiles is multipart (file upload) - these are different from the rest so don't want people copying the wrong pattern
- remove the TODO comment I left at the top of the file once examples are in

### Inputs & outputs
Just editing docs/API.md, adding curl examples + example responses. No code changes.

### Risks & unknowns
Not 100% sure if I should also document PUT /profiles/{profile_id} and GET /reviews/{review_id}/status since those exist in the code but aren't in the docs at all right not, might be out of scope for this issue, might ask about it.

### Edge cases
Mainly just don't mess up the login and profile creation examples since they're not plain JSON like everything else.
