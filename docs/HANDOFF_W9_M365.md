# Handoff: Week 9 → Microsoft 365 GPT 5.6

**Repo path:** `docs/HANDOFF_W9_M365.md`  
**Branch:** `chore/128-add-dependency-vulnerability-scans`  
**Issue:** [#128 — Add a dependency vulnerability scan to the CI pipeline](https://github.com/ascherj/pathreview/issues/128)  
**Status:** M365 Prompt A accepted as Option E and verified locally (`pip-audit==2.10.1`, `npm audit --omit=dev --audit-level=high` exit 0). CI + JOURNAL Check-in 1 updated after that advice.

Companion facts (shorter): [`WEEK9_HANDOFF.md`](WEEK9_HANDOFF.md)  
Upload packs + prompts: [`m365-bundles/`](m365-bundles/)

---

## Why M365 (cost)

Keep Cursor for planning, verifying claims against the repo, and applying the chosen fix. Use **Microsoft 365 GPT 5.6** for long-form policy reasoning, audit triage prose, and first-draft PR/JOURNAL text so those tokens are not spent re-reading the tree in a fresh Cursor subagent.

---

## What to upload (in order)

Work from the PathReview clone root:

`m3/w7/pathreview/`  
(absolute: `/Users/watney/git/zimmnotes/chat/codepath/ai201/m3/w7/pathreview`)

| Step | File to upload | Prompt source |
|------|----------------|---------------|
| 1 (policy — do first) | `docs/m365-bundles/01-ci-policy-and-issue.md` | Prompt A in `docs/m365-bundles/M365_PROMPTS.md` |
| 2 (triage) | `docs/m365-bundles/02-audit-findings-triage.md` | Prompt B |
| 3 (writing) | `docs/m365-bundles/03-pr-and-journal-drafts.md` | Prompt C |

If the chat only accepts a tiny upload, use **`docs/m365-bundles/00-fallback-smallest.md`** with Prompt A (abbreviated), then add `02` once policy is chosen.

Raw local audit dumps (also inlined into the bundles): `_audit_scratch/`.

---

## How to run each M365 turn

1. Open a **new** M365 chat for Prompt A (keeps context small).
2. Upload the matching bundle `.md`.
3. Paste the **entire** prompt block from `M365_PROMPTS.md` (Prompt A / B / C).
4. Save the reply (file or clipboard).
5. Paste the reply back into the Cursor session with a short note, e.g.  
   `M365 Prompt A reply — use this as policy input; do not implement until I confirm.`

Do **not** ask M365 to invent file paths or “fix the whole Week 9 project” without the bundles — it will hallucinate CI that does not match this fork.

---

## Verified facts M365 must treat as ground truth

1. Draft jobs `dependency-audit-python` / `dependency-audit-frontend` already exist in `.github/workflows/ci.yml`.
2. **`pip audit` fails locally** with `ERROR: unknown command "audit"` even on pip 26.2 — CI must install/run **`pip-audit`**.
3. **`pip-audit` finds 2 vulns with empty fix lists:** `chromadb` (PYSEC-2026-311 / GHSA-f4j7-r4q5-qw2c), `ecdsa` (PYSEC-2026-1325 / GHSA-wj6h-64fc-37mp).
4. **`npm audit --audit-level=high` exits 1** on the current lockfile (5 high + 1 critical among 11).
5. After **`npm audit fix` (no `--force`)** in a temp tree: still fails high gate; remaining blockers include **vitest (critical)** / **vite (high)** needing a **semver-major** force upgrade; react-router still flagged on 6.30.4.
6. Unrelated noisy `make check` / `make test-unit` is **out of scope** for #128.
7. Branch already contains `upstream/main`. No GitHub PR yet. Local `gh` auth token was invalid — run `gh auth login` before opening the PR.

---

## What to bring back to Cursor

Paste, ideally as three labeled sections:

1. **Policy choice** — option letter from Prompt A + exact YAML snippet recommended  
2. **Triage** — what to commit in this PR vs follow-up (lockfile? Vite major? `--ignore-vuln`?)  
3. **Drafts** — PR body + JOURNAL Week 9 Check-in 1/2 text (Cursor will verify and edit before commit)

Then say whether to **implement**, **commit**, and/or **open a draft PR**.

---

## Intentionally not done yet

- No change to `ci.yml` beyond the existing draft  
- No `make audit` target  
- No lockfile / dependency upgrades  
- No JOURNAL Week 9 fill-in  
- No PR

---

## After M365 (Cursor checklist)

- [ ] Confirm policy with you  
- [ ] Patch CI (+ optional Makefile/docs) to match decision  
- [ ] Re-run local `pip-audit` / `npm audit --audit-level=high` and record results  
- [ ] Fill JOURNAL Week 9; open **draft** PR early  
- [ ] `gh auth login` if needed; push; submit branch URL via course portal when ready
