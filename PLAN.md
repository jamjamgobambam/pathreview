## Solution plan

**Issue:** API reference doc is missing the `POST /profiles` request body schema #89 (https://github.com/ascherj/pathreview/issues/89)

### Understand
The documentation in `docs/API.md` does not explain request body schemas. Users cannot see what parameters to send when calling `POST /profiles` or `POST /reviews`. We must add tables and examples for these request bodies.

### Map
The following files are involved:
- [API.md](file:///Users/nataliechan/Desktop/codePath/ai210/pathreview/docs/API.md) (The documentation file to edit)
- [profiles.py](file:///Users/nataliechan/Desktop/codePath/ai210/pathreview/api/routes/profiles.py) (Defines profiles endpoint parameters)
- [reviews.py](file:///Users/nataliechan/Desktop/codePath/ai210/pathreview/api/routes/reviews.py) (Defines reviews endpoint parameters)

### Plan
1. Check the request parameters for profile creation in `api/routes/profiles.py`.
2. Check the request schemas for review creation in `api/routes/reviews.py`.
3. Add multipart request body table and example to `docs/API.md` for `POST /profiles`.
4. Add JSON request body table and example to `docs/API.md` for `POST /reviews`.

### Inputs & outputs
- Input: Route parameters and Pydantic schemas in code.
- Output: Tables and examples in `docs/API.md`.

### Risks & unknowns
- If developers change `ProfileCreate` in `api/schemas/profile.py`, the documentation in `docs/API.md` will not match the code.
- If developers change `create_profile_endpoint` in `api/routes/profiles.py`, the documentation will not match the code.

### Edge cases
- Users do not need to send `resume_file` in `api/routes/profiles.py`. The documentation must show what happens when users omit this file.
- The endpoint `create_profile_endpoint` in `api/routes/profiles.py` rejects file types that are not PDF or Markdown. The documentation must explain this rule.
- The field `profile_id` in `api/schemas/review.py` must be a UUID. The documentation must show this format.

