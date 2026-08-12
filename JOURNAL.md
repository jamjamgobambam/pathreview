## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Issue #106 addresses a missing shared test fixture: `tests/fixtures/sample_profiles/basic_profile.json`. The fixture was removed, causing tests that depend on reusable sample profile data to lack a consistent input containing GitHub information, resume details, and repository examples. I verified that the `tests/fixtures/` directory is missing and that `tests/conftest.py` currently only provides resume and README fixtures. The fix will restore a standard sample profile fixture so tests can use consistent data and avoid duplicated setup.

### Is This Issue Right for Me?

- **Understanding** — I verified the missing fixture issue by inspecting the test structure and confirmed that shared sample profile data needs to be restored.
- **Tier Fit** — This is a Tier 1 issue that matches my current experience because it is a focused test infrastructure change involving adding missing fixture data rather than modifying production behavior.
- **Scope** — Small and well-bounded: restore one shared sample profile fixture (`tests/fixtures/sample_profiles/basic_profile.json`). No production code changes are required.
- **Effort (Time)** — Reasonable for Weeks 8–9. The work involves creating realistic sample data, matching the expected profile structure, and running the test suite.
- **Dependencies** — None external. The fixture uses static test data and does not require database changes, API keys, or external services.
- **Verification** — I can validate the change by running `make test-unit` and confirming the related tests pass.

**Branch name:** `test/106-restore-basic-profile-fixture`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/michellejtan/pathreview/commit/ae1dde81f3ef04a4d660c08fbc644f05b2b701af

**Reproduction summary:**
Ran `ls tests/fixtures` and `find tests -iname "*profile*"` — confirmed the
`tests/fixtures/sample_profiles/basic_profile.json` file and its parent folder
do not exist anywhere in the repo, and no test currently imports it. The only
remaining reference is a TODO comment in `scripts/run_evals.py` pointing at
that path, suggesting the fixture was removed (or never committed) at some
point and the reference was left behind.

**PLAN.md link:** https://github.com/michellejtan/pathreview/blob/test/106-restore-basic-profile-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
No existing test or code consumes `basic_profile.json` today, so there's no schema to match
exactly — I derived the shape from the `Profile` model fields and the issue's "GitHub
username, resume, two repos" wording, but a reviewer may expect different field names.
Separately, `IngestedSource` (the model repos map to) has no `name`/`description` fields, so
my `repos` shape doesn't correspond 1:1 to any existing DB model — flagging this in case it
should be reconciled before merging.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the full solution from PLAN.md. Restored
`tests/fixtures/sample_profiles/basic_profile.json` with a fake portfolio (GitHub username,
resume text, two repos), but revised the shape partway through to match what the ingestion
parsers actually consume rather than an arbitrary guess: resume text now uses section
headings (`Summary`, `Technical Skills`, `Experience`, `Education`) matching
`ResumeParser.SECTION_HEADERS`, and each repo entry uses GitHub API-style fields
(`html_url`, `language`, `stargazers_count`, `forks_count`, `open_issues_count`, `pushed_at`,
`readme_content`) matching what `RepoAnalyzer.parse()` reads. Added a `sample_profile_data`
fixture to `tests/conftest.py` and a new test file, `tests/unit/test_fixtures.py`, that loads
the fixture and asserts on its shape.

Before starting, I ran `make test-unit` and `make check` on `main` to record a baseline: 53
pre-existing test failures (376 passing) and 182 pre-existing lint errors, all unrelated to
this issue. After my changes, both commands show the same pre-existing counts plus my new
test passing — confirmed by stashing my changes and re-running both commands to verify the
baseline numbers matched exactly.

**Next steps:**
Open a draft PR using the repo's PR template, share it in the cohort Slack channel for peer
review, and address any feedback before marking it ready for review.

**Blockers:**
None currently. (One snag along the way: the local pre-commit hook's `mypy` check caught two
missing type annotations — `disallow_untyped_defs = true` — in the new test function and the
`sample_profile_data` fixture. `make check`'s `typecheck` target doesn't cover `tests/`, so
this wasn't visible until commit time; fixed by adding explicit annotations.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/669

**Branch:** `test/106-restore-basic-profile-fixture`

**What you built:**
Restored the missing `basic_profile.json` test fixture with a realistic fake portfolio shaped
to match the actual ingestion parsers (resume section headers, GitHub-style repo metadata),
and wired it up via a `sample_profile_data` pytest fixture plus a test proving it loads
correctly.

**Tests added or updated:**
`tests/unit/test_fixtures.py` (new) — asserts `sample_profile_data` has the expected
top-level profile fields and exactly two repo entries, each with `name`, `html_url`, and
`readme_content`.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
(Both pass in the sense that my changes introduce zero new failures beyond the documented
53 pre-existing test failures and 182 pre-existing lint errors — see PR description for the
before/after comparison.)

**Draft PR feedback received from:** none [to be filled in after peer review, posted in Slack already]

**PR description (copy, for offline verification):**

> **Summary**
> The PR restores a missing test fixture file at `tests/fixtures/sample_profiles/basic_profile.json` that is referenced by `scripts/run_evals.py` and `scripts/issues_manifest.json`. The fixture contains realistic fake portfolio data (GitHub username, resume text, two repository entries) structured to match what the actual ingestion parsers consume.
>
> **Issue**
> Closes #106
>
> **Changes**
> - Introduces `tests/fixtures/sample_profiles/basic_profile.json` containing fake profile data with fields like `github_username`, `resume_filename`, `resume_text` (with section headers such as Summary, Technical Skills, Experience, Education), `portfolio_url`, and two `repos` entries patterned after GitHub API metadata
> - Adds a `sample_profile_data` fixture to `tests/conftest.py` following established patterns for loading sample data
> - Creates `tests/unit/test_fixtures.py` with a test that validates the fixture loads properly and contains expected structure (profile fields present, exactly two repos, each containing `name`/`html_url`/`readme_content`)
>
> **Testing**
> Unit tests pass with 53 pre-existing failures remaining unchanged; new test passes. Integration tests not applicable. Linting produces no new errors (182 pre-existing unchanged). Type checking passes. Manual verification involves confirming the JSON fixture contains appropriate fields and running the new test.
>
> **Screenshots / Demo**
> N/A — test fixture only, no UI change.
>
> **Notes for Reviewers**
> No integration test currently uses this fixture. The two repository entries mirror raw GitHub API metadata rather than the `IngestedSource` database model, as that represents the layer where parsing occurs before database mapping.

(Note: as of this writing the PR is still in Draft and the Testing section above still needs
the concrete manual-verification steps promised — this copy will be refreshed once those
edits land on GitHub.)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]
no feedback

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
The fixture itself was trivial to write, but figuring out the *right* shape for it wasn't.
Since no test or production code currently imports `basic_profile.json`, there was no
existing schema to match — just a TODO comment and the issue's loose "GitHub username,
resume, two repos" description. I initially guessed at field names, then realized partway
through that I should reverse-engineer the shape from what `ResumeParser` and
`RepoAnalyzer` actually consume (section headers, GitHub API-style repo fields) instead of
inventing something arbitrary. That revision cost more time than the original write-up, and
it surprised me that a "just add a missing file" issue turned out to be way more ambiguous than I expected

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
In my own projects I'd never think twice about picking field names for test data. 
The names in the project are implicitly a contract with parsing code I didn't write and couldn't fully
predict from the issue alone. I also got into the habit of leaning on make check / make test-unit as a baseline. Running them first showed there were already 53 test failures and 182 lint errors, so I could compare against that and know my changes weren’t adding anything new. It was a lot better than just eyeballing things and thinking they “looked fine.” That kind of before-and-after checking feels like a habit you really need in a large codebase, and I had to keep that habit  of checking pre-existing failures before touching any codes.

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI was most useful for the mechanical parts — scaffolding the JSON fixture, the
`sample_profile_data` conftest fixture, and the test asserting on its shape once I knew what
shape I wanted. It fell short on the actual judgment call of *what* that shape should be:
figuring out that I needed to go read `ResumeParser.SECTION_HEADERS` and
`RepoAnalyzer.parse()` directly, rather than trust a plausible-looking guess, was something I
had to push for myself. It also didn't catch the `mypy` `disallow_untyped_defs` gap in my new
test code — that only surfaced when the pre-commit hook ran at commit time, since `make
check`'s typecheck target doesn't cover `tests/`.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I'd go straight to reading the parser code before writing the first draft of the fixture,
instead of writing a plausible-looking version first and revising it once I realized it
didn't match what was actually consumed downstream. I'd also open the draft PR and post to
Slack earlier in the week rather than at the very end, since as of this reflection I'm still
waiting on review and lost the chance to iterate on feedback within the module.

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
Catching that my `repos` shape didn't correspond 1:1 to the `IngestedSource` DB model and
flagging it explicitly in both PLAN.md and the PR notes, instead of quietly shipping a
mismatch. It would have been easy to call the fixture "done" once the JSON looked
reasonable; verifying it against the actual parsing code and Calling out the one place where it still didn’t line up felt more honest.