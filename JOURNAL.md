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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I implemented the fix in `docs/API.md`. Working from PLAN.md, I added a request
body section under both endpoints:

- `POST /profiles` — noted it's `multipart/form-data` (not JSON), added a field
  table for `github_username`, `portfolio_url`, and `resume_file` with types and
  required/optional, plus a `curl -F` example.
- `POST /reviews` — noted it's a JSON body, added a field table with `profile_id`
  (UUID, required), plus a `curl` JSON example.

I double-checked every field name and type against the code (`api/routes/` and
`api/schemas/`) so the docs match reality. On my open question — the route also
accepts plain text uploads — I documented "PDF or Markdown" to match the docstring
and the 422 error message users actually see, rather than an incidental accepted
type.

**Next steps:**

Open a draft PR, get peer/mentor feedback, then mark it ready for review and fill
in the PR template. Run `make check` and `make test-unit` to confirm no new
failures (docs-only change, so no code tests to add).

**Blockers:**

None.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/626]

**Branch:** `docs/89-api-request-body-schemas`

**What you built:**

Added the request body schemas for `POST /profiles` and `POST /reviews` to
`docs/API.md` — field tables (name, type, required/optional) and copy-paste
`curl` examples — so a developer can call either endpoint without reading the
backend code.

**Tests added or updated:**

None — this is a docs-only change to `docs/API.md`. No runtime behavior changes,
so there is nothing to unit-test.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [ none ]

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ x ] No — still awaiting review

**Summary of feedback:**

No review came in. PR #626 has been open since August 3 with no review comments,
no line comments, and no requested reviewers. It's still open and unmerged. I
checked the Files changed and Conversation tabs again this week to confirm.

**How you responded:**

Nothing to respond to, so I left the PR alone. I did re-read my own diff while
waiting and re-checked the field names and types in `docs/API.md` against
`api/schemas/profile.py`, `api/schemas/review.py`, and the routes, so the PR is
still accurate if a maintainer picks it up later. If feedback does come in, I'd
reply in the thread and push a new commit on `docs/89-api-request-body-schemas`
rather than force-pushing over the history.

---

### Reflection

**What was harder than you expected?**

I picked a Tier 1 docs issue partly because I thought writing down what an
endpoint takes would be mechanical. The writing was the easy part; figuring out
what was actually true took longer. `POST /profiles` is `multipart/form-data`
with a file upload, not JSON like the endpoints around it, so I couldn't copy the
pattern from the neighboring sections and had to read the route signature in
`api/routes/profiles.py`.

**What did you learn about working in a large codebase?**

In my own projects I'm the source of truth — if I forget how something works I
just change it. Here the code was the authority and I was writing about it, so
every line had to be checkable against `api/routes/` or `api/schemas/`. Instead
of writing what seemed reasonable, I did it one field at a time: write the field,
open the schema, confirm the name, type, and whether it's required.

I also learned the existing conventions count as part of the task. I matched the
heading style and table format already in `docs/API.md` even where I'd have laid
it out differently, since a docs PR that reads like a different author is harder
to merge. Running `make check` and `make test-unit` on a docs-only change felt
pointless at first, until I realized it's there to show I didn't break anything,
not to test my diff.

**How did AI tools help — and where did they fall short?**

AI helped most with orientation and formatting. When I was picking the issue I
used it to find where profile and review handling lived so I wasn't grepping
blind, and later to draft the field tables and the `curl -F` example once I'd
given it the fields. That saved a lot of time on markdown formatting.

Where it fell short was the part that mattered. When I asked about the request
body for `POST /profiles`, it gave me a clean JSON body, which is wrong — the
endpoint is form-data with a file. It looked right because it matched the rest of
the API, and if I'd pasted it in I'd have written docs worse than no docs, since
a reader would trust them. The plain text vs. PDF/Markdown question was similar:
AI could tell me what the code accepts, but not what the maintainer meant, and
that was the actual decision. It was good for "where is this" and "format this."
I had to check "is this true" myself.

**What would you do differently if you started over?**

I'd open the draft PR earlier. I did the reproduction, wrote PLAN.md, and
finished the change before opening PR #626 in Week 9, so my open question about
plain text vs. PDF/Markdown sat in my journal for a week instead of somewhere a
maintainer could see it. In a draft PR in Week 8 it might have gotten an answer.

Related to that, I'd ask open questions on the issue thread instead of deciding
quietly and explaining afterward. I still think my call was right, but I made it
alone when there was an easy way not to. I'd keep the issue choice — Tier 1 docs
was the right first contribution to a repo I didn't know, and it still made me
read real backend code.

**What are you most proud of from this module?**

Catching that `POST /profiles` is form-data and not JSON instead of taking the
answer that looked right. It would have been easy to use the JSON body AI gave
me, or to assume it matched the endpoints around it, and nothing would have
caught it — docs have no tests, `make check` passes either way, and no reviewer
has looked at the PR. The only check was me opening `api/routes/profiles.py` and
reading the signature. That's the habit I'm keeping from this module more than
the PR itself.