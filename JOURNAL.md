# PathReview — Module 3 Journal

Running record of progress across Weeks 7–10.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/128

**Issue title:** Add a dependency vulnerability scan to the CI pipeline

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

PathReview currently runs lint, typecheck, unit, integration, and frontend tests in GitHub Actions, but nothing checks whether installed Python or JavaScript dependencies contain known security vulnerabilities. That means a dependency with a published CVE could ship without CI noticing. The fix adds automated scanning to `.github/workflows/ci.yml`: `pip audit` for Python dependencies (after installing the project with dev extras) and `npm audit` for the frontend (after `npm ci`), failing the build when high-severity findings are detected. This is DevOps/CI work rather than application logic, but it directly improves the project's security posture and gives contributors faster feedback on risky dependency updates.

**Branch name:** `chore/128-add-dependency-vulnerability-scans`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue claim comment:** https://github.com/ascherj/pathreview/issues/128#issuecomment-5034547950

**Cohort ledger entry:** Yie Sheng Chen · `speculaas` · #128 · [cohort spreadsheet](https://docs.google.com/spreadsheets/d/1oclK-70-klhGofiaw6krk8-zV_wZiumsR-Xnd_l5ZR8/edit?gid=1079392097#gid=1079392097)

### "Is this right for me?" checklist reasoning

| Question | Assessment |
|---|---|
| **Is it actually open?** | Yes — listed in the open issue export and issue tracker with no linked merged PR. |
| **Is the scope clear?** | Yes — add `pip audit` and `npm audit` to CI, fail on high-severity findings, primary file is `ci.yml`. |
| **Is it the right size?** | Tier 3, estimated 3–5 hours. Larger than Tier 1, but bounded to one workflow file plus policy decisions. |
| **Is the maintainer active?** | Yes — upstream repo has recent merges and active issue activity. |
| **Does it match my skill level?** | Chosen deliberately to learn CI/GitHub Actions YAML. I accept the Tier 3 scope because my primary goal is DevOps/CI experience, not the fastest Tier 1 PR. |

**Scope reasoning:** I considered Tier 1 alternatives (#37 snapshot tests, #159 structlog/caplog) for lower risk, but selected #128 because it is the most direct path to editing GitHub Actions workflows, configuring audit tools, and iterating through the CI feedback loop. Main risks: existing dependencies may already have advisories, Python and npm audit tools differ in severity filtering, and policy choices (blocking threshold, job structure) need investigation before the PR is merge-ready.

**Supporting reference:** See `docs/issue-128-context.md` for Mermaid diagrams, CI design notes, and implementation roadmap from issue-selection discussions.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/speculaas/pathreview/commit/474ab43e5c8060948355504d054e8bee3aac25e5

**Reproduction summary:**
Issue #128 is a missing CI security gate rather than a runtime app bug. I reproduced it by inspecting `.github/workflows/ci.yml` on `main`: the workflow has lint, typecheck, unit, integration, and frontend jobs only — no `pip audit`, `npm audit`, or any vulnerability-scan step. Search for those terms returns no matches, which matches the issue’s claim that Python and JavaScript dependencies are not automatically audited. Full notes are in `docs/reproduction-128.md` on that commit.

**PLAN.md link:** https://github.com/speculaas/pathreview/blob/chore/128-add-dependency-vulnerability-scans/PLAN.md

**Walkthrough video (recommended):** *(optional — not recorded yet; not graded)*

**Blockers or open questions:**
- Will existing dependencies already fail `pip audit` / `npm audit --audit-level=high` on first enablement?
- Should Python use plain `pip audit` (any finding fails) or a pinned tool with severity filtering to mirror npm’s high/critical policy?
- Is documenting local `make audit` / SETUP commands in-scope for the PR, or should the first PR touch only `ci.yml`?

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I already had draft Python and frontend dependency-audit jobs on this branch from earlier weeks. This week I reproduced the real local scanner behavior: `pip audit` is not a valid built-in pip command here (CI must install and run `pip-audit`), the frontend full-tree `npm audit --audit-level=high` fails on existing high/critical findings (including Vite/Vitest), and `pip-audit` reports two Python advisories with no listed fix versions (`chromadb`, `ecdsa`). I captured the evidence under `_audit_scratch/`, wrote an M365 handoff/bundles for policy review, and locked a mergeable policy after verifying commands locally: pin `pip-audit==2.10.1` against runtime deps with two explicit `--ignore-vuln` IDs, and run `npm audit --omit=dev --audit-level=high` so the blocking gate covers production frontend deps without forcing a Vite major upgrade into this PR.

**Next steps:**
Watch GitHub Actions on the PR, trim the PR description if needed, ask for peer/mentor Slack feedback, submit the branch URL via the course portal, and keep JOURNAL Check-in 2 current.

**Blockers:**
None for opening the PR. Remaining Vite/Vitest remediation and React Router moderate findings are follow-ups. Temporary Python `--ignore-vuln` entries need maintainer acceptance.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/828

**Branch:** `chore/128-add-dependency-vulnerability-scans`

**What you built:**
Added two blocking CI jobs for issue #128: `dependency-audit-python` installs runtime deps and runs pinned `pip-audit==2.10.1` (with two documented temporary ignores for currently unfixed advisories), and `dependency-audit-frontend` runs `npm audit --omit=dev --audit-level=high` after `npm ci`. Updated local parity docs and Week 9 notes so contributors can reproduce the same gate.

**Tests added or updated:**
No application unit tests — this is CI/docs. Validation: local `pip-audit` with the two ignores (exit 0) and `npm audit --omit=dev --audit-level=high` (exit 0). Evidence: `_audit_scratch/option-e-verified.txt`, `_audit_scratch/npm-audit-omit-dev.txt`. Confirm the new Actions jobs on the PR.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes  
Pre-existing baseline noise remains on this tree (~182 ruff findings; unit suite previously had many failures/errors). This PR only changes workflow YAML and documentation — it does not modify application source — so “passes” means no new application-suite failures were introduced (per course guidance for documented pre-existing failures).

**Draft PR feedback received from:** none yet (opened as ready-for-review PR #828; will note Slack peer/mentor when received)

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No formal reviewer or maintainer comments had arrived on [PR #828](https://github.com/ascherj/pathreview/pull/828) when I wrote this reflection. Summer 2026 course notes say formal reviewer feedback is not part of this term, so the empty review queue is expected rather than a blocker. I did post a peer-review request in Slack asking classmates familiar with GitHub Actions or dependency security to look at the PR; I had not received a Slack reply to document by the time of this entry.

**How you responded:**
No reviewer-requested code changes were required. I did a final self-review of `.github/workflows/ci.yml`, the PR description source (`docs/PR_BODY_128.md`), local audit evidence under `_audit_scratch/`, and the Week 9 journal entries. If maintainer or peer comments arrive later, I will reply professionally and update this section.

---

### Reflection

**What was harder than you expected?**
Defining a useful, mergeable vulnerability *policy* was harder than writing the GitHub Actions YAML. The issue sounded simple—run Python and JavaScript audits and fail on high-severity findings—but local runs showed the first design would not work as intended.

The draft Python job ran `pip audit` after upgrading pip, yet `pip audit` is not a valid command in this environment. The scanner is the separate `pip-audit` package, and CI must install and invoke it explicitly (we pinned `pip-audit==2.10.1`).

The scans also exposed advisories that already existed in the tree. Two Python findings (`PYSEC-2026-311` for `chromadb`, `PYSEC-2026-1325` for `ecdsa`) had no listed fix versions. Clearing the remaining frontend high/critical development-tool findings would have required a breaking Vite/Vitest major upgrade (`npm audit fix --force`). That shifted the work from a small workflow edit into decisions about production vs development scope, severity thresholds, temporary exceptions, and PR boundaries—without using `continue-on-error` or `|| true` to fake a green gate. The final policy blocks production-dep audits, documents two narrow Python ignores, and leaves the Vite migration as follow-up.

**What did you learn about working in a large codebase?**
A focused change still has to respect repository conventions, existing debt, and what maintainers can reasonably review. In my own projects I can revise deps, CI, and docs together; here each extra surface expands review scope and regression risk.

Issue #128 points at `.github/workflows/ci.yml`, but implementing it correctly also meant reading `pyproject.toml`, frontend package metadata and lockfile, sibling CI jobs, CONTRIBUTING/SETUP, audit output, and the PR template. A short audit command is meaningless without knowing how deps are installed and which packages are production vs tooling.

I also learned that unrelated baseline failures are not automatically my issue. Local `make check` / `make test-unit` were already noisy on this tree. My job was to compare baseline vs branch and show the workflow/docs change did not add application-suite failures—not to turn #128 into broad lint/test cleanup. CI jobs are executable project behavior: their exit codes gate merges, so thresholds and exceptions deserve the same care as application logic.

**How did AI tools help — and where did they fall short?**
AI helped most when work was split by role. Cursor could see the full repo and was useful for locating files, checking history, running audits, applying focused edits, and verifying the workflow against real command output. Microsoft 365 Copilot helped with longer policy analysis, CI concept explanations, audit triage, and drafting reviewer-facing text without spending as much Cursor generation quota.

That loop worked when each side stayed in its lane: Copilot proposed options such as a production-focused gate; Cursor had to verify them. Copilot’s suggested `pip-audit` pin was not authoritative until Cursor confirmed `2.10.1` from a local install and confirmed `npm audit --omit=dev --audit-level=high` exited 0.

AI fell short wherever suggestions were treated as facts without running commands. Early drafts assumed upgrading pip would expose `pip audit`. Models also cannot decide what maintainers will accept as security policy—that needs repo evidence, exit codes, scope judgment, and honest documentation. The reliable pattern became: ask for options → execute and inspect → correct unsupported claims → record only what the tree demonstrates. Short decision handoffs beat pasting entire transcripts.

**What would you do differently if you started over?**
I would run the real audit commands as soon as I claimed the issue. The biggest unknown was whether current dependencies already violated the proposed gate. Finding that earlier would have exposed the policy problem before planning around the invalid `pip audit` command.

I would also separate verified facts from proposed decisions sooner: inspect the workflow → confirm the missing jobs → install/identify real tools → record versions, findings, and exit codes → classify prod vs dev → ask for policy advice with that evidence → implement the smallest defensible gate → open a draft PR earlier for visibility, then mark ready after verification.

Finally, I would pass shorter decision summaries between Copilot and Cursor—verified facts, chosen option, rejected alternatives, and required checks—instead of full reasoning dumps.

**What are you most proud of from this module?**
I am most proud that I did not treat the first red scans as a reason to hide failures or force a breaking frontend migration into a CI-gate PR. I investigated why the jobs failed, corrected the Python command, separated runtime deps from tooling, and chose a blocking policy with narrow, documented exceptions.

The change is small in file count but changes project behavior: before PR #828, CI checked quality and functionality but not dependency advisories; afterward, separate Python and frontend jobs enforce a documented baseline and make failures visible by ecosystem. I am also proud that I can explain *why* that policy exists, what it does *not* cover (full-tree Vite/Vitest remediation), and what follow-up should remove the temporary ignores.
