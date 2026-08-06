## Solution plan

**Issue:** Add a bias audit report that runs over a sample of stored reviews  
**Link:** https://github.com/ascherj/pathreview/issues/72

### Understand

The project already has bias detection logic in `safety/bias_detector.py`, but there is no offline audit script at `scripts/audit_bias.py`. What we want is that a contributor can run a script that samples stored reviews, passes each review through `BiasDetector.detect_bias(text)`, and produces a clear report about possible bias results. What is actually happening is that the detector can analyze one text string at a time, but there is no script that runs it over stored review data or summarizes false positive and false negative patterns.

### Map

Files I expect to inspect or touch:

- `scripts/audit_bias.py`: add the script.
- `safety/bias_detector.py`: reuse `BiasDetector.detect_bias(text)` method
- `scripts/run_evals.py`: use as a nearby example for script structure.
- `scripts/seed_db.py`: inspect sample review data shape if the script needs seeded reviews.
- `tests/`: add or update tests if need be

Important functions or modules:

- `BiasDetector.detect_bias(text)`: returns `(is_biased, reason)`.
- `structlog.get_logger()`: existing safety files use structured logging for detected safety events.

### Plan

1. Inspect the stored review model and seed data to find a reliable source of review text.
2. Create `scripts/audit_bias.py` with a `main()` function that loads up to 100 review records.
3. For each review, call `BiasDetector.detect_bias(text)` and store the result, reason, and review identifier.
4. Produce a report that summarizes total reviews checked, detected bias count, reasons, and any known false positive or false negative labels when available.
5. Add focused tests or sample-run verification so the script behavior can be checked before opening a pull request.

### Inputs & outputs

Input:

- Stored review text from the local database, seeded data, or another project-approved sample source.
- Optional expected labels if a review sample includes ground-truth bias labels.

Output:

- A readable audit report from `scripts/audit_bias.py`.
- Summary counts for reviews checked and bias detections.
- Reason-level breakdowns from `BiasDetector.detect_bias(text)`.
- False positive and false negative counts if ground-truth labels are available.

### Risks & unknowns

- I still need to confirm the best source for stored review text.
- The issue asks for false positive and false negative rates, but the current repo may not include ground-truth labels for stored reviews.
- If there is no labeled dataset, the script may need to report detected bias patterns first and leave false positive/negative rates as unavailable.
- The script should not duplicate bias detection logic that already exists in `BiasDetector`.

### Edge cases

- No reviews exist in the local database.
- A review has empty or missing text.
- More than 100 reviews exist, so the script should sample or limit results consistently.
- `BiasDetector.detect_bias(text)` returns `False` with an empty reason.
- The report should still run if every sampled review is non-biased or every sampled review is flagged.
