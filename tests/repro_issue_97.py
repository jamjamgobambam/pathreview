"""
Reproduction script for issue #97:
  Review progress indicator doesn't update in real time during long-running reviews

Stdlib-only static check of the full progress-reporting path.
All 4 checks are expected to FAIL, confirming the bug exists.

Run with:
  python tests/repro_issue_97.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent

checks_passed = 0
checks_failed = 0


def check(description: str, result: bool, failure_note: str) -> None:
    global checks_passed, checks_failed
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {description}")
    if not result:
        print(f"         -> {failure_note}")
        checks_failed += 1
    else:
        checks_passed += 1


print("\nReproducing issue #97: progress indicator gap\n")

# ---------------------------------------------------------------------------
# Check 1: Review DB model has a progress_pct column
# ---------------------------------------------------------------------------
print("1. Backend model — core/models/review.py")
model_src = (ROOT / "core/models/review.py").read_text()
check(
    "Review model defines a progress_pct column",
    "progress_pct" in model_src and "mapped_column" in model_src.split("progress_pct")[1][:60],
    "No progress_pct column found. getattr(review, 'progress_pct', 0) always returns 0.",
)

# ---------------------------------------------------------------------------
# Check 2: process_review writes progress_pct during processing
# ---------------------------------------------------------------------------
print("\n2. Review service — core/services/review_service.py")
service_src = (ROOT / "core/services/review_service.py").read_text()
check(
    "process_review updates progress_pct during processing",
    "progress_pct" in service_src,
    "process_review never writes progress_pct — progress stays 0 throughout.",
)

# ---------------------------------------------------------------------------
# Check 3: get_review_status returns dynamic progress, not a hardcoded 0
# ---------------------------------------------------------------------------
print("\n3. API route — api/routes/reviews.py")
route_src = (ROOT / "api/routes/reviews.py").read_text()
check(
    "get_review_status returns a real progress value (not getattr fallback of 0)",
    'getattr(review, "progress_pct", 0)' not in route_src,
    "Route uses getattr fallback — always returns progress_pct=0 regardless of state.",
)

# ---------------------------------------------------------------------------
# Check 4: Frontend Review type includes progress_pct
# ---------------------------------------------------------------------------
print("\n4. Frontend type — frontend/src/types/index.ts")
types_src = (ROOT / "frontend/src/types/index.ts").read_text()
check(
    "Review interface includes progress_pct field",
    "progress_pct" in types_src,
    "progress_pct missing from Review interface — frontend silently drops it.",
)

# ---------------------------------------------------------------------------
# Check 5: ReviewPage renders a progress bar, not just a static spinner
# ---------------------------------------------------------------------------
print("\n5. Review page — frontend/src/pages/ReviewPage.tsx")
page_src = (ROOT / "frontend/src/pages/ReviewPage.tsx").read_text()
check(
    "ReviewPage renders a progress bar during polling (not only a Loader spinner)",
    "progress_pct" in page_src or "progressBar" in page_src or "progress-bar" in page_src,
    "ReviewPage only renders <Loader> spinner — no progress bar shown during processing.",
)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(
    f"\n{checks_passed + checks_failed} checks total"
    f" — {checks_passed} passed, {checks_failed} failed"
)

if checks_failed > 0:
    print("\nIssue confirmed: progress_pct is dropped at every layer of the stack.")
    sys.exit(1)
else:
    print("\nAll checks passed — issue appears to be fixed.")
    sys.exit(0)
