# Solution Plan

**Issue:** [Add a bias audit report that runs over a sample of stored reviews #72](https://github.com/ascherj/pathreview/issues/72)

---

## Understand

**Expected behavior:** A script `scripts/audit_bias.py` should sample up to 100 stored reviews from the database, run each review's text content through `BiasDetector.detect_bias()`, log results with structlog, and produce a summary report showing false positive/negative rates broken down by demographic signal type (dismissive educational background language vs. demographic assumptions).

**Actual behavior:** The script does not exist. `BiasDetector` in `safety/bias_detector.py` is fully implemented and returns `(is_biased: bool, reason: str)`, but it is never called in an offline/batch context. The only safety check in the codebase (`_run_safety_checks` in `core/services/review_service.py`) does not use `BiasDetector` at all — it only validates structure. There is no way for maintainers to audit how the bias detector performs across stored reviews.

**Root cause:** The script was planned but never implemented. The gap is purely additive — no existing code needs to change, only `scripts/audit_bias.py` needs to be created.

---

## Map

**Files to read (no changes needed):**
- `safety/bias_detector.py` — `BiasDetector.detect_bias(text)` returns `(bool, str)`; patterns split into `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS`
- `core/models/review.py` — `Review` model; relevant fields: `id`, `sections` (JSON), `status`, `overall_score`
- `core/database.py` — `AsyncSessionLocal`, `init_db` — how other scripts connect to the DB
- `scripts/seed_db.py` — pattern for how scripts use `asyncio.run()` + `AsyncSessionLocal`

**File to create:**
- `scripts/audit_bias.py` — the audit script

**Files that may need minor updates:**
- `JOURNAL.md` — Week 8 section
- `PLAN.md` — this file (living document)

---

## Plan

1. **Set up DB connection and sample reviews**
   - Use `AsyncSessionLocal` following the pattern in `scripts/seed_db.py`
   - Query `Review` table for records with `status="complete"` (only completed reviews have `sections` content)
   - Use `LIMIT 100` with `ORDER BY RANDOM()` to get a random sample

2. **Extract text content from reviews**
   - Each review's `sections` field is a JSON list of `FeedbackSection` dicts with `section_name`, `content`, `suggestions`
   - Concatenate `content` and `suggestions` fields into a single text blob per review for analysis
   - Handle `None` sections gracefully

3. **Run bias detector on each review**
   - Call `BiasDetector.detect_bias(text)` for each review
   - Log each result with structlog: `review_id`, `is_biased`, `reason`, signal category
   - Track which pattern category triggered: `dismissive` vs `demographic` based on the `reason` string

4. **Compute audit metrics**
   - Count total reviews sampled
   - Count flagged reviews overall
   - Count flagged by signal category (dismissive / demographic)
   - Since we have no ground truth labels, report flag rates rather than true false positive/negative rates — note this limitation in the report output

5. **Produce and print the report**
   - Print a structured summary to stdout using structlog or plain print
   - Include: sample size, total flagged, flag rate, breakdown by signal type
   - Write optional JSON report to `scripts/audit_report.json`

---

## Inputs & Outputs

**Input:**
- Live PostgreSQL database (via `DATABASE_URL` from `.env`)
- Up to 100 `Review` records with `status="complete"` and non-null `sections`

**Output:**
- Structured log lines via structlog for each reviewed item
- Final printed report showing:
  - Sample size
  - Total flagged count and percentage
  - Dismissive pattern flag count
  - Demographic pattern flag count
- Optional: `scripts/audit_report.json` with full results

---

## Risks & Unknowns

- **No ground truth labels:** The seeded reviews in `seed_db.py` use placeholder content ("Analysis of technical skills...") that will not trigger any bias patterns. The audit will report 0 flags on seed data — this is expected, but makes it hard to verify the script works correctly without injecting test cases with known-biased text.
  - Mitigation: Add 2–3 synthetic reviews with known-biased text at the top of the script for validation, clearly marked as test fixtures.

- **Async database access:** All DB operations in this codebase use `async`/`await` with `AsyncSessionLocal`. The script must use `asyncio.run()` correctly — following `seed_db.py` as the pattern.

- **`sections` field format:** Reviews store sections as a list of dicts. If a review was processed with an older schema or failed mid-processing, `sections` may be `None` or malformed. Must handle gracefully.

- **Sample size:** If fewer than 100 complete reviews exist in the DB, the script should sample all available and note the actual count.

---

## Edge Cases

- Reviews with `sections=None` (pending or failed reviews) — skip, don't crash
- Reviews with empty `sections=[]` — skip, log a warning
- Database has fewer than 100 complete reviews — sample all available, report actual count
- A review's section `content` is an empty string — skip that section, continue
- `BiasDetector.detect_bias()` raises an unexpected exception — catch, log, continue to next review
- Script run with no complete reviews in DB — report 0 samples, exit cleanly with a message
