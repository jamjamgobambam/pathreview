# Week 9 verified facts (do not re-derive)

**Start here for M365 upload instructions:** [`HANDOFF_W9_M365.md`](HANDOFF_W9_M365.md)

Date: 2026-08-03
Branch: chore/128-add-dependency-vulnerability-scans
Issue: https://github.com/ascherj/pathreview/issues/128

## Already done on branch
- Draft CI jobs `dependency-audit-python` / `dependency-audit-frontend` exist (commit 239ac1f).
- PLAN.md, reproduction doc, JOURNAL Weeks 7–8 done.
- Branch includes upstream/main (no unique upstream commits to rebase).
- No PR opened yet (`gh` token invalid — run `gh auth login`).

## Load-bearing findings (verified locally)
1. **`pip audit` is broken as drafted.** Even with pip 26.2, `pip audit` returns `ERROR: unknown command "audit"`. CI must install/run the `pip-audit` package (`pip install pip-audit` then `pip-audit`).
2. **Python audit currently fails:** `chromadb 1.5.9` → PYSEC-2026-311 / GHSA-f4j7-r4q5-qw2c (no fix versions listed); `ecdsa 0.19.2` → PYSEC-2026-1325 / GHSA-wj6h-64fc-37mp (no fix versions). Exit code 1.
3. **npm gate fails on current lockfile:** `npm audit --audit-level=high` exit 1 — 5 high + 1 critical among 11 total.
4. **After `npm audit fix` (no --force) in a temp tree:** drops to 6 vulns meta `{moderate:4, high:1, critical:1}` — **still fails `--audit-level=high`**. Remaining notable: esbuild/vite/vitest chain (moderate, needs Vite 8 / `--force`); react-router 6.30.4 still flagged (range includes through 7.17.0).
5. Unrelated baseline suite red is out of scope per PLAN.

## Recommended default strategy for Cursor orchestrator (pending M365 + user confirm)
- Fix Python job to use pinned `pip-audit`.
- Prefer documented `--ignore-vuln` for the two unfixed PyPI IDs OR ask maintainers — silent `continue-on-error: true` is not acceptable.
- Include safe `npm audit fix` lockfile refresh if it materially helps; clear remaining high/critical without a Vite major if possible; if not possible, decide with maintainers whether moderate-only residual + upgraded RR is enough or whether policy should stay red until Vite upgrade (follow-up).
- Add optional `make audit` + short SETUP note in a separate commit.
- Open **draft PR early**; fill JOURNAL Week 9 Check-in 1 now; Check-in 2 at submission.

## M365 offload
See `docs/m365-bundles/M365_PROMPTS.md`. Upload bundles; paste replies back for review.
