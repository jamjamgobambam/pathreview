# M365 GPT 5.6 prompts (Week 9 · PathReview #128)

**Handoff (how to use this folder):** [`../HANDOFF_W9_M365.md`](../HANDOFF_W9_M365.md)

Upload the matching bundle `.md` from this folder, then paste the prompt.
Paste **M365 replies back into Cursor** for verification before any implementation commit/PR.

---

## Prompt A — Policy research

**Upload:** `01-ci-policy-and-issue.md` (+ optionally `02-audit-findings-triage.md` if already generated)

```text
You are advising on GitHub Actions dependency audits for PathReview issue #128.

Facts already verified locally (treat as ground truth, do not re-litigate):
1. Draft CI already adds jobs dependency-audit-python and dependency-audit-frontend.
2. Frontend: `npm audit --audit-level=high` exits 1 today — 11 vulns (5 high, 1 critical).
3. `npm audit fix --dry-run` proposes ~30 package bumps (no --force); esbuild/vite/vitest still need --force (breaking Vite major) for moderate chain.
4. Python: plain `pip audit` is NOT a built-in command on current pip unless `pip-audit` is installed. The drafted job may fail with "unknown command audit" unless it installs pip-audit (or uses `pip-audit` CLI).
5. pip-audit CLI has `--ignore-vuln ID` but no npm-style `--audit-level=high`.
6. Issue asks to fail the build on high-severity findings. Primary file named: `.github/workflows/ci.yml`.
7. Unrelated baseline `make check` / `make test-unit` debt is OUT OF SCOPE.

Decide and recommend ONE mergeable Week 9 strategy:
A) Gate only (accept red audit jobs until deps fixed separately) — bad for mergeability
B) Gate + non-breaking `npm audit fix` lockfile update so high/critical clear; document remaining moderate vite/esbuild
C) Gate + broader dep upgrades including Vite major
D) Gate with temporary documented exceptions / continue-on-error — usually unacceptable for #128
E) Other (specify)

Also recommend exact Python CI step(s):
- install `pip-audit` vs rely on `pip audit`
- whether to pin a version
- how to approximate “high+” policy (fail-any vs ignore list)

Output format:
1. Recommended option letter + 5-bullet rationale
2. Exact YAML snippet for the two jobs (copy-paste ready)
3. What belongs in this PR vs follow-up
4. Risks / maintainer questions for the PR description
5. What NOT to do
```

---

## Prompt B — Audit triage

**Upload:** `02-audit-findings-triage.md`

```text
Triage these local audit artifacts for PathReview #128.

Goals:
1. Classify each npm finding: fixable with `npm audit fix` (no --force), requires --force/breaking, or false-positive/dev-only noise.
2. After a no-force fix, which high/critical remain?
3. Is updating package-lock.json in-scope for a CI-gate PR that must be green, or should it be a linked follow-up?
4. For Python: given pip-audit help flags in the bundle, propose the safest CI invocation that still matches “fail on high-severity” intent as closely as tools allow.
5. Propose a short “Notes for Reviewers” paragraph explaining asymmetry between npm --audit-level=high and Python tooling.

Be concrete: package names, severity, and recommended action. No fluffy summary.
```

---

## Prompt C — PR + JOURNAL drafts

**Upload:** `03-pr-and-journal-drafts.md`

```text
Draft student coursework text for CodePath AI201 Week 9. Match the repo PR template and JOURNAL Week 9 headings exactly.

Constraints:
- Issue: ascherj/pathreview#128
- Branch: chore/128-add-dependency-vulnerability-scans
- Author voice: first person, concise, technical, no hype
- Document pre-existing lint/unit suite noise as out of scope if relevant
- Do not invent a PR URL — leave a placeholder
- Assume implementation matches the PLAN plus whatever CI/lockfile policy is chosen (note assumptions clearly at top)

Produce:
1. Full PR description filling Summary / Issue / Changes / Testing / Notes for Reviewers
2. JOURNAL.md “## Week 9 — Solution building & PR submission” with Check-in 1 and Check-in 2 skeletons (Check-in 1 = mid-week progress; Check-in 2 = final with PR placeholder)
3. A 5-item self-review checklist tied to CONTRIBUTING conventions

Mark any unverified claim with [VERIFY].
```
