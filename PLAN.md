# Solution Plan

**Issue:** API response for profile creation doesn't include the `profile_id` field:  
https://github.com/jamjamgobambam/pathreview/issues/78

## Understand

**Root Cause:** The profile creation response model, `ProfileResponse` in `api/schemas/profile.py`, exposes the record's primary key only as `id`. The underlying database model (`core/models/profile.py`) also stores the primary key in the `id` column, and the route builds the response using `ProfileResponse.model_validate(new_profile)`. Because `ProfileResponse` doesn't define a `profile_id` field, it never appears in the serialized response.

**Expected vs. Actual**

- **Actual:** `POST /profiles` returns `{"id": ..., "user_id": ..., "github_username": ..., "portfolio_url": ..., "created_at": ..., "resume_filename": ...}` with no `profile_id`.
- **Expected:** The response also includes a `profile_id` field containing the same identifier so clients can immediately use it with endpoints such as `GET /profiles/{profile_id}`.

**Key Constraint:** `ProfileResponse` uses `model_config = {"from_attributes": True}` and is populated via `model_validate(new_profile)` from the ORM object. The ORM object has an `id` attribute but **does not** have a `profile_id` attribute. Simply adding `profile_id: UUID` to the schema would therefore fail validation because Pydantic has no source attribute to populate it from. The fix must derive `profile_id` from the existing `id` field rather than expecting a new ORM attribute.

## Map

**Files Involved**

- `api/schemas/profile.py` — `ProfileResponse` (the only production file that should require changes).
- `api/routes/profiles.py` — `create_profile_endpoint`, which builds the response using `ProfileResponse.model_validate(...)`. Also verify that `get_profile_endpoint` and `update_profile_endpoint`, which reuse the same schema, continue to work correctly.
- `core/models/profile.py` — `Profile` model, which confirms that the primary key attribute is `id`.
- `tests/unit/test_profile_schema.py` — new test file created during reproduction that will contain assertions validating the fix.

## Plan

1. **Confirm the Reproduction (done).** `tests/unit/test_profile_schema.py` validates a Profile-like object using `ProfileResponse` and asserts that `profile_id` is present and equal to `id`. This test currently fails.
2. **Expose `profile_id` in `ProfileResponse`.** Add a `profile_id` field that maps to the model's existing `id` value. The preferred approach is a Pydantic `@computed_field` that returns `self.id`, which is straightforward and backward compatible. Another option is to use `validation_alias="id"`. Keep the existing `id` field so current clients are not broken.
3. **Verify the Route Layer.** Confirm that `create_profile_endpoint`, along with the GET and UPDATE endpoints that reuse `ProfileResponse`, correctly includes `profile_id` when validating ORM objects and that the generated OpenAPI schema documents the new field.
4. **Update and Expand Test Coverage.** Make the reproduction test pass and add an assertion that `id` is still present to preserve backward compatibility.
5. **Run Project Checks.** Ensure `make check` (Ruff, Black, and MyPy) and `make test-unit` both pass before opening the PR.

## Inputs and Outputs

**Input:** A persisted `Profile` ORM object (or equivalent object with an `id` attribute) passed to `ProfileResponse.model_validate(...)`.

**Output:** The serialized `ProfileResponse` now includes a `profile_id: UUID` field whose value matches `id`. The JSON returned by `POST /profiles` (and by the GET and PUT endpoints that reuse the same schema) changes from:

```json
{"id": ...}
```

to:

```json
{"id": ..., "profile_id": ...}
```

No request schemas (`ProfileCreate` or `ProfileUpdate`) are modified. The OpenAPI response schema also gains a `profile_id` property.

## Risks and Unknowns

- **Attribute Mapping.** Because `ProfileResponse` is populated with `from_attributes=True`, a plain `profile_id: UUID` field would fail validation due to the missing ORM attribute. Using `@computed_field` or `validation_alias` avoids this issue, and the reproduction test verifies the behavior.
- **Serialization Behavior.** Confirm that the chosen implementation appears in `model_dump()`, `model_dump_json()`, and the generated OpenAPI schema by asserting against the serialized output, not just the Python attribute.
- **Backward Compatibility.** Replacing `id` with `profile_id` could break existing clients. Before considering that approach, search `frontend/src/` and any API consumers for references to `.id`. The current plan is additive and keeps both fields.
- **Shared Response Schema.** Since `ProfileResponse` is used by the create, get, and update endpoints, the change affects all three responses. This should be acceptable because it only adds a new field, but it should still be verified.

## Edge Cases

- **Optional Fields.** A profile with no resume, `github_username`, or `portfolio_url` should still include a valid `profile_id`. The identifier is always required, regardless of optional fields.
- **Consistent Identifiers.** `profile_id` must always match `id`. The implementation should derive one from the other rather than storing duplicate values.
- **UUID Serialization.** Both `id` and `profile_id` should serialize to the same UUID string in JSON.
- **Shared Endpoints.** Responses from `GET /profiles/{id}` and `PUT /profiles/{id}` should also include `profile_id`, not just `POST /profiles`.