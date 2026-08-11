# Collect 3 M365 upload artifacts for lint/test-failure triage

Run these from the PathReview repo root **on the machine where `make check` / `make test-unit` already fail** (your remote with `.venv`).

Goal: produce **exactly 3 text files** that fit M365 GPT 5.6’s upload limit, so Copilot can triage failures without you dumping the whole suite.

```bash
mkdir -p bundles/failure-triage
cd /path/to/pathreview   # your pathreview root

# ---------------------------------------------------------------------------
# ARTIFACT 1 — Failure INDEX (counts + top signatures, not full logs)
# ---------------------------------------------------------------------------
{
  printf '%s\n' '# PathReview failure triage index'
  printf '%s\n' "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '%s\n' "Branch: $(git branch --show-current)"
  printf '%s\n' "HEAD: $(git rev-parse --short HEAD)"
  printf '%s\n' ''
  printf '%s\n' '## Your Module 3 branch files (for attribution)'
  git diff main --name-only 2>/dev/null || git diff origin/main --name-only
  printf '%s\n' ''
  printf '%s\n' '## Ruff summary (rule counts)'
  .venv/bin/ruff check . --output-format=concise 2>&1 \
    | tee bundles/failure-triage/ruff-raw.txt \
    | awk -F: '{print $NF}' \
    | sed 's/^ *//' \
    | awk '{print $1}' \
    | sort | uniq -c | sort -nr \
    | head -40
  printf '%s\n' ''
  printf '%s\n' '## Ruff by directory (top paths)'
  awk -F: 'NF>=2 {print $1}' bundles/failure-triage/ruff-raw.txt \
    | sed 's#/[^/]*$##' \
    | sort | uniq -c | sort -nr \
    | head -30
  printf '%s\n' ''
  printf '%s\n' '## Pytest failures only (node ids)'
  LLM_PROVIDER=mock .venv/bin/pytest tests/unit -q --tb=no 2>&1 \
    | tee bundles/failure-triage/pytest-summary.txt \
    | grep -E 'FAILED|ERROR|passed|failed' \
    | head -80
  printf '%s\n' ''
  printf '%s\n' '## Failed test file counts'
  grep '^FAILED' bundles/failure-triage/pytest-summary.txt \
    | awk '{print $2}' \
    | cut -d: -f1 \
    | sort | uniq -c | sort -nr
} > bundles/failure-triage/01_failure_index.md

# ---------------------------------------------------------------------------
# ARTIFACT 2 — Sample DETAILS (one failure per cluster, truncated)
# ---------------------------------------------------------------------------
{
  printf '%s\n' '# PathReview failure sample details'
  printf '%s\n' 'Purpose: representative stacks only — not every failure.'
  printf '%s\n' ''
  printf '%s\n' '## Ruff: first 40 lines (style of errors)'
  head -40 bundles/failure-triage/ruff-raw.txt
  printf '%s\n' ''
  printf '%s\n' '## Pytest: first 8 failed tests with short traceback'
  LLM_PROVIDER=mock .venv/bin/pytest tests/unit -q --tb=short \
    --maxfail=8 2>&1 | head -200
  printf '%s\n' ''
  printf '%s\n' '## Related open issues (from local export if present)'
  if test -f ../pathreview-open-issues.json; then
    python3 - <<'PY'
import json, pathlib
p = pathlib.Path('../pathreview-open-issues.json')
data = json.loads(p.read_text())
keys = ('test', 'lint', 'ruff', 'mock', 'structlog', 'caplog', 'async')
for issue in data:
    title = issue.get('title','').lower()
    labels = ' '.join(l['name'] for l in issue.get('labels', []))
    blob = title + ' ' + labels
    if any(k in blob for k in keys) or 'tier-1' in labels and 'tests' in labels:
        labs = ','.join(l['name'] for l in issue['labels'])
        print(f"#{issue['number']}: {issue['title']} [{labs}]")
PY
  else
    printf '%s\n' '(pathreview-open-issues.json not found next to repo)'
  fi
} > bundles/failure-triage/02_failure_samples.md

# ---------------------------------------------------------------------------
# ARTIFACT 3 — Context + QUESTION for Copilot (scope constraints)
# ---------------------------------------------------------------------------
{
  printf '%s\n' '# Ask Copilot: triage baseline failures vs issue #128'
  printf '%s\n' ''
  printf '%s\n' '## Situation'
  printf '%s\n' '- Course: AI201 Module 3 PathReview'
  printf '%s\n' '- Chosen issue: #128 Add dependency vulnerability scan to CI'
  printf '%s\n' '- Branch changes: ci.yml audit jobs, JOURNAL.md, docs/issue-128-context.md, vite host:true'
  printf '%s\n' '- Local: make check → 182 ruff errors; make test-unit → 53 failed / 375 passed'
  printf '%s\n' '- Week 7 selection/setup is done; I need a triage plan, NOT a mandate to fix all 182+53'
  printf '%s\n' ''
  printf '%s\n' '## Please answer'
  printf '%s\n' '1. Are these failures likely baseline/upstream vs caused by my #128 branch?'
  printf '%s\n' '2. Cluster the lint rules and failed tests into 5–10 buckets with likely root causes.'
  printf '%s\n' '3. Map buckets to existing GitHub issues if possible (esp. #158, #159, fixture issues).'
  printf '%s\n' '4. Compare effort: fix-all-failures vs reviewing ~66 issues with gh export — which is larger?'
  printf '%s\n' '5. Recommend a minimal Week 8–9 plan for #128 only (what to ignore, what to verify).'
  printf '%s\n' '6. Suggest make/check commands that validate ONLY my changed files.'
  printf '%s\n' '7. Produce Mermaid flowchart: triage → ignore / track-issue / fix-for-#128.'
  printf '%s\n' ''
  printf '%s\n' '## Constraints'
  printf '%s\n' '- Do not invent file contents not in uploads.'
  printf '%s\n' '- Prefer categorization and decision trees over rewriting the whole codebase.'
  printf '%s\n' '- Plain-text Mermaid blocks preferred.'
} > bundles/failure-triage/03_copilot_prompt_and_context.md

# Size check
wc -c bundles/failure-triage/01_failure_index.md \
     bundles/failure-triage/02_failure_samples.md \
     bundles/failure-triage/03_copilot_prompt_and_context.md
wc -w bundles/failure-triage/01_failure_index.md \
     bundles/failure-triage/02_failure_samples.md \
     bundles/failure-triage/03_copilot_prompt_and_context.md
```

Upload these three:

1. `01_failure_index.md`
2. `02_failure_samples.md`
3. `03_copilot_prompt_and_context.md`

If any file is huge, shrink Artifact 2 first (`--maxfail=5`, `head -100`).
