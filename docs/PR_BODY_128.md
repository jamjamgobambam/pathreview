# PR draft for ascherj/pathreview#128

Push from a machine with working GitHub auth, then open against **upstream** `ascherj/pathreview` `main`:

```bash
cd m3/w7/pathreview
git push -u origin HEAD
# if gh works:
gh pr create --repo ascherj/pathreview \
  --base main \
  --head speculaas:chore/128-add-dependency-vulnerability-scans \
  --title "ci: add dependency vulnerability scans (#128)" \
  --body-file docs/PR_BODY_128.md
```

Course portal branch URL after push:
https://github.com/speculaas/pathreview/tree/chore/128-add-dependency-vulnerability-scans

---

## Summary

Adds blocking CI jobs that scan Python runtime dependencies with pinned `pip-audit` and frontend production dependencies with `npm audit --omit=dev --audit-level=high`. This closes the missing security gate described in #128 without forcing a Vite/Vitest major upgrade into the same PR.

## Issue

Closes #128

## Changes

- Add `dependency-audit-python`: install runtime package (`pip install -e .`), pin `pip-audit==2.10.1`, fail on findings except two temporary `--ignore-vuln` IDs that currently have no fix versions (`PYSEC-2026-311` / `chromadb`, `PYSEC-2026-1325` / `ecdsa`).
- Add `dependency-audit-frontend`: `npm ci` then `npm audit --omit=dev --audit-level=high` (production deps only).
- Document local parity commands in `docs/reproduction-128.md` and `docs/SETUP.md`.
- Record Week 9 journal progress and the Option E policy decision in `PLAN.md` / `JOURNAL.md`.

## Testing

- [x] Local: `pip-audit --ignore-vuln PYSEC-2026-311 --ignore-vuln PYSEC-2026-1325` → exit 0 (2 ignored)
- [x] Local: `npm audit --omit=dev --audit-level=high` → exit 0 (2 moderate `react-router` findings only; non-blocking under `--audit-level=high`)
- [ ] GitHub Actions: confirm both new jobs appear and pass on this PR
- [ ] Unit tests / linter: **pre-existing noise** on this tree (~182 ruff issues; unit suite previously noisy with failures/errors). This PR only changes CI YAML and docs — it does not modify application code. Please treat “passes” as “introduces no new application failures.”

## Screenshots / Demo

N/A — CI configuration change. Evidence: `_audit_scratch/option-e-verified.txt`, `_audit_scratch/npm-audit-omit-dev.txt`.

## Notes for Reviewers

- The earlier draft `pip audit` step is invalid here even after upgrading pip; the job installs/runs the separate `pip-audit` package.
- Python has no npm-style `--audit-level=high` in the CLI we used; fail-any plus two named temporary ignores is the closest mergeable policy.
- Frontend blocking gate is **production-scoped** on purpose. Full-tree `npm audit --audit-level=high` still fails today because of Vite/Vitest high/critical findings that require a semver-major (`npm audit fix --force` → Vite 8). That remediation should be a follow-up.
- React Router currently reports moderate advisories under production audit and does **not** fail `--audit-level=high`; still worth a follow-up upgrade.
- Please confirm whether temporary Python ignores + production-only npm scope are acceptable for merge; otherwise we can widen the gate after dep remediation lands.
