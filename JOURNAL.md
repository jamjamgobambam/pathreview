## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/89)

**Issue title:** API reference doc is missing the POST /profiles request body schema


**Tier:** [ x ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The API docs (docs/API.md) list all the endpoints but don't show what data you
need to send when calling POST /profiles and POST /reviews. Right now you'd have
to read the backend code to figure out the fields. POST /profiles is confusing
because it takes form-data with a file upload (github_username, portfolio_url,
and an optional resume file), not JSON. POST /reviews just needs a JSON body
with one field: profile_id. The fix is to add both request bodies to docs/API.md
with a simple table of fields and an example, so anyone can use the API without
reading the code.

**Why this issue / selection notes:**

I picked this Tier 1 docs issue because I'm still getting comfortable with the
codebase, and documentation work lets me learn how the API is built without
risking any runtime behavior. The scope is small and safe — I only edit one
file, docs/API.md.

Working through the "Is this right for me?" checklist:

- I can explain it in my own words: the API docs list the endpoints but don't
  show what data to send to POST /profiles and POST /reviews. The fix adds that
  info with a simple table and an example.
- I found and read the code it affects: the schemas in api/schemas/ and the
  routes in api/routes/. I confirmed POST /profiles takes form-data with a file
  upload (not JSON), and POST /reviews takes JSON with one field, profile_id.
- I know what "done" looks like: before, a developer has to read the code to
  know what to send; after, the docs tell them directly.
- Scope and time: the edit takes under an hour, plus some time double-checking
  the fields against the code. That fits the Tier 1 range and the deadline.
- No blockers, and since it's docs-only there's no code to unit-test.


**Branch name:** [docs/89-api-request-body-schemas]

**Setup confirmation:** [ x ] App runs locally at localhost:5173

**Cohort ledger:** [ x ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/0d410be3fc40a684f262b446f5ab8f24fe8f4a4f

**Reproduction summary:**

This is a docs issue, so reproducing it means showing the missing info is really
absent and pointing to where. I opened `docs/API.md` and confirmed that
`POST /profiles` (line 18) and `POST /reviews` (line 24) each have just a
one-line description and no request body — no fields, no example. You can't call
either endpoint without reading the code. I then checked the code to confirm
what the docs should say:

- `POST /profiles` takes form-data (not JSON): `github_username` and
  `portfolio_url` (both optional text) and an optional `resume_file` (PDF or
  Markdown). Confirmed in `api/routes/profiles.py` and `api/schemas/profile.py`.
- `POST /reviews` takes JSON with one required field, `profile_id`. Confirmed in
  `api/schemas/review.py` and `api/routes/reviews.py`.

So the gap is real: the docs stop at endpoint names and never show the request
bodies. It lives at `docs/API.md:18` and `docs/API.md:24`.

**Reproduction steps:**

1. Open `docs/API.md` and look at lines 18 and 24 — one sentence each, no
   request body.
2. Try to call either endpoint from the docs alone — you can't tell `/profiles`
   is form-data or that `/reviews` needs `profile_id`.
3. Check the code to see the real fields: `api/routes/profiles.py`,
   `api/routes/reviews.py`, and the schemas in `api/schemas/`.

**PLAN.md link:** [https://github.com/nvpai/pathreview/blob/docs/89-api-request-body-schemas/PLAN.md]

**Walkthrough video (recommended):** [optional Loom link]

**Blockers or open questions:**

Small one: `api/routes/profiles.py` also accepts plain text uploads, but the
docstring says only PDF/Markdown. I'm not sure yet whether the new docs should
mention plain text or just match the PDF/Markdown intent.

