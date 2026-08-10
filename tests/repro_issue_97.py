"""
Reproduction script for issue #97:
"Review progress indicator doesn't update in real time during long-running reviews"
https://github.com/ascherj/pathreview/issues/97

This script documents and confirms the bug WITHOUT needing the full stack
(DB, sqlalchemy, node). It statically inspects the source files that make up
the progress-reporting data path and asserts on the exact gaps that cause the
static "Analyzing your portfolio..." spinner to be shown instead of a live
progress bar.

Run from the repo root:

    python tests/repro_issue_97.py

Expected result BEFORE the fix: all four checks report FAIL, proving the bug.
After the fix (Week 9) the same checks should report PASS.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def check(name: str, condition: bool, explain: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        print(f"        -> {explain}")
    return condition


def main() -> int:
    model = read("core/models/review.py")
    service = read("core/services/review_service.py")
    ts_types = read("frontend/src/types/index.ts")
    review_page = read("frontend/src/pages/ReviewPage.tsx")

    results = []

    # Backend layer -----------------------------------------------------------
    # The status endpoint returns getattr(review, "progress_pct", 0), but the
    # Review model has no such column, so the value is *always* 0.
    results.append(check(
        "Review model defines a progress_pct column",
        "progress_pct" in model,
        "core/models/review.py has no progress_pct column, so the status "
        "endpoint's getattr(review, 'progress_pct', 0) can only ever return 0.",
    ))

    # process_review never writes progress at any step (ingestion, agent, RAG).
    results.append(check(
        "process_review updates progress_pct during processing",
        "progress_pct" in service,
        "core/services/review_service.py transitions pending->processing->"
        "complete but never sets progress_pct between steps, so no intermediate "
        "progress is ever emitted.",
    ))

    # Frontend layer ----------------------------------------------------------
    # The Review TS type omits progress_pct, so the field returned by the API is
    # silently dropped before it can reach the component.
    results.append(check(
        "Review TypeScript type includes progress_pct",
        "progress_pct" in ts_types,
        "frontend/src/types/index.ts Review interface omits progress_pct, so the "
        "value from GET /reviews/{id}/status is dropped in the hook.",
    ))

    # ReviewPage renders a static spinner instead of a percentage-driven bar
    # during the polling state.
    polling_block = review_page.split("isPolling &&", 1)[-1].split("currentReview?.status", 1)[0]
    results.append(check(
        "ReviewPage renders a progress bar (not just a spinner) while polling",
        "progress_pct" in polling_block,
        "frontend/src/pages/ReviewPage.tsx shows an animate-spin Loader with the "
        "text 'Analyzing your portfolio...' during isPolling and never references "
        "progress_pct, so the user sees no real-time progress.",
    ))

    print()
    if all(results):
        print("All checks PASS -- issue #97 appears fixed.")
        return 0
    failed = results.count(False)
    print(f"{failed}/{len(results)} checks FAIL -- issue #97 reproduced. "
          "Progress is reported nowhere along the path, so the UI is stuck on a "
          "static spinner.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
