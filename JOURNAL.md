## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `extract_skills()` function in the ingestion pipeline scans portfolio
text to detect which languages and tools a candidate has used. It
correctly detects Python, DevOps tools, and databases, but fails entirely
on JavaScript (returns no detections for clear JS code) and only
partially detects TypeScript (matches "React" but misses TypeScript
itself, even when the text references .ts/.tsx files). I confirmed this
locally: `extract_skills()` returned `[]` for a JavaScript sample and
only `['React']` for a TypeScript sample. A correct fix will add the
missing detection patterns for JS/TS so they're reported like every
other supported language, without changing how existing Python/DevOps
detection behaves.

**Branch name:** fix/148-skill-extractor-js-ts-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger