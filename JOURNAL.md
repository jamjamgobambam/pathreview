## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

https://github.com/biswaskdk/pathreview/commit/xxxxxxxx

**Reproduction summary:**

I confirmed that PathReview currently supports resumes and GitHub repositories but does not support portfolio website URLs. There is no web parser or pipeline support for website ingestion.

**PLAN.md link:**

https://github.com/biswaskdk/pathreview/blob/feature/portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

I need to understand how the existing ingestion pipeline sends parsed content to the vector store.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the portfolio website ingestion path by adding a dedicated web parser, wiring it into the ingestion pipeline, and hardening README heading parsing for indented markdown content. The new regression test now covers extracting readable portfolio text from HTML and passes.

**Next steps:**
I am validating the changed parser and pipeline behavior in the project environment and documenting the remaining repo-level baseline failures separately from the new portfolio fix.

**Blockers:**
The repository's `make` shell wrapper is not available in this Windows environment, so validation is being confirmed through the project's `.venv` Python toolchain instead.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/758

**Branch:**
`feature/portfolio-url-ingestion`

**What you built:**
The fix adds a `WebParser` for portfolio HTML content and exposes `IngestionPipeline.ingest_web(...)` so website pages can flow through the same chunking and embedding path as resumes and READMEs. It also wires real portfolio-URL fetching (async `httpx`) into the review service's ingestion path and normalizes README heading extraction to support indented markdown headers.

**Tests added or updated:**
I added `tests/unit/test_web_parser.py`, which exercises HTML portfolio extraction (title, body text, metadata) and empty-page handling.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> "Passes" here means my changes introduce **no new failures**. This repository has documented pre-existing baseline failures that are unrelated to my change (see note below).

**Pre-existing baseline failures (unrelated to this change):**
Before my changes, `make test-unit` reported **53 failed / 375 passed**; `make check` reported 52 files needing `black`, 177 `ruff` errors, and `mypy` aborting on a numpy stub incompatibility. After my changes the suite is **51 failed / 379 passed** — my change adds no new failures and actually fixes 2 pre-existing README parser tests. `ruff` and `black` pass cleanly on every file I added or modified.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. As of the end of Week 10, [PR #758](https://github.com/ascherj/pathreview/pull/758) is still **open** with no reviews, no review comments, and no maintainer comments — only my original PR description. Per the Summer 2026 course note, reviewer feedback is not part of this term, so there is nothing to respond to.

**How you responded:**
No reply was required. I re-read my own diff one more time while waiting and confirmed the PR body still accurately describes the change, including the pre-existing baseline failure counts (53 failed / 375 passed before → 51 failed / 379 passed after). If feedback does arrive later, the two things I expect to be asked about are (1) whether raw-HTML string stripping in `WebParser` should be replaced with a real parser like BeautifulSoup, and (2) SSRF hardening on the user-supplied portfolio URL in `core/services/review_service.py`, since I fetch it with `httpx` without restricting the target host. I would agree with both and would treat the URL validation one as a blocking fix rather than a follow-up.

---

### Reflection

**What was harder than you expected?**

Separating *my* failures from *the repo's* failures. I assumed "run the tests, see green, ship it," but the first `make test-unit` run gave me 53 failures before I had touched a single line. Most of Week 9 was spent proving a negative — capturing a clean baseline, re-running after my change, and diffing the counts — instead of writing code. Two of my "failures" turned out to be pre-existing README parser tests that my regex change actually *fixed*, which I only noticed because I had the before-numbers written down.

The environment was the other tax. `make` doesn't exist in my Windows shell, so every command in `CONTRIBUTING.md` had to be translated into a direct `.venv` invocation, and `mypy` aborted entirely on a numpy stub incompatibility (`Type statement is only supported in Python 3.12+`) that had nothing to do with me. Deciding "this is not mine, document it and move on" was uncomfortable — it feels like an excuse until you have the numbers to back it.

I also underestimated how much of the work was *reading*. My Week 8 plan listed three files to modify. The real change touched four, and one of them (`core/services/review_service.py`) I hadn't predicted at all — I only found it because the portfolio path had a placeholder sitting there waiting to be filled in.

**What did you learn about working in a large codebase?**

In my own projects I decide the shape of things. Here the shape was already decided, and my job was to notice it. `ingest_web(profile_id, url, content)` looks the way it does because `ingest_resume` and `ingest_readme` already looked that way — same content-hash dedup, same skip check, same chunk → embed → record-source sequence. The correct move was to make my method boring and predictable rather than better. Same with `WebParser`: `CONTRIBUTING.md` has an explicit "Adding a New Parser" section, so the right answer was to implement `BaseParser`, register it in the pipeline, and add a unit test — the path was already paved.

The other lesson is that blast radius matters more than elegance. The one-character-ish change I'm least comfortable with is the `^\s*(#{1,6})` regex in `readme_parser.py`. It's a two-line fix, it made two existing tests pass, and it's still the riskiest thing in the PR, because it changes behavior for an input path (READMEs) that has nothing to do with the feature I was asked to build. In my own project I'd have just fixed it. Here I had to call it out explicitly in the PR body so a reviewer could push back. Writing a PR description is part of the engineering, not paperwork after it.

**How did AI tools help — and where did they fall short?**

Most useful: orientation and mechanical scaffolding. Asking "where does parsed content get handed to the vector store" got me to `ingestion/pipeline.py` and the parser registry in minutes instead of an afternoon of grep. It was also good at pattern-matching a new method onto three existing sibling methods, and at drafting the unit test skeleton and the PR body structure.

Where it fell short:

- **It couldn't tell me what was already broken.** Only actually running the suite and recording the baseline did that. AI would happily explain a failing test as though it were my fault.
- **It's over-eager to expand scope.** Suggestions kept drifting toward "also add BeautifulSoup," "also add retry logic," "also add caching." Deciding that the PR should be *one* feature plus its test was a judgment call I had to make and defend.
- **Environment reality.** No amount of asking fixed the missing `make` wrapper or the numpy/mypy stub issue; I had to work out the `.venv` equivalents myself and then decide those failures were out of scope.
- **Taste about risk.** Nothing flagged the README regex change as the scariest part of the diff. That came from me thinking about who else depends on that code path.

**What would you do differently if you started over?**

1. **Capture the baseline in Week 8, not Week 9.** Running `make test-unit` and `make check` on a clean checkout and pasting the raw counts into `PLAN.md` would have removed the single biggest source of anxiety later.
2. **Write a more honest plan.** My `PLAN.md` step 3 is literally "Fetch the webpage" — that hid the real decisions (async vs sync client, where in the request lifecycle the fetch happens, what to persist on `IngestedSource`). It also listed `api/schemas/profile.py` as a file to change, which I ended up not needing, and missed `review_service.py`, which I did. A plan that names the *seams* would have been worth more than one that names the files.
3. **Keep the README regex fix out.** It's unrelated to portfolio ingestion. A separate small PR would have been cleaner and easier to review, even though it does make two tests pass.
4. **Handle the edge cases I listed and then didn't implement.** My plan enumerated timeouts, redirects, 404s, and invalid URLs. The shipped code handles the empty page and leans on `httpx` defaults for the rest. I should have either implemented them or explicitly scoped them out in writing instead of quietly dropping them.
5. **Push the branch earlier.** I sat on local work longer than necessary; an early draft PR would have made the diff visible and reviewable sooner.

**What are you most proud of from this module?**

Not shipping a defensible excuse. When the suite was red before I started, the tempting options were to hide it ("tests pass") or to hide behind it ("the repo is broken, can't verify"). Instead I measured the before and after, wrote the exact numbers into both the PR body and this journal, showed that my change moved the count in the right direction, and confirmed `ruff` and `black` are clean on every file I touched. That's the habit I actually want to keep — being specific about what I verified and honest about what I didn't.