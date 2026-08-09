"""Reproduce issue #150: tech detector counts vendored/build files as source.

TechDetector's skip logic in `_should_skip_file` (agent/tools/tech_detector.py)
matches directory names with a leading slash (e.g. "/node_modules/"), so it
only filters paths where node_modules/build/vendor appear *nested* under
something else. A path rooted at the repo root -- "node_modules/..." or
"build/..." -- has no leading slash before the directory name, so it is never
skipped and still counts toward language detection.

Usage:
    python -m scripts.repro_issue_150

See: https://github.com/ascherj/pathreview/issues/150
"""

from agent.tools.tech_detector import TechDetector

# Exact reproduction from the issue body.
FILES = [
    "main.py",
    "core/app.py",
    "node_modules/lib/index.js",
    "node_modules/lib/util.js",
    "node_modules/x/a.js",
    "node_modules/y/b.js",
    "build/bundle.js",
    "build/vendor.js",
]


def main() -> None:
    detector = TechDetector()
    result = detector.execute({"files": FILES})
    primary = result.data["primary_language"]

    print(f"Files given: {len(FILES)} (2 authored Python files, 6 vendored/build JS files)")
    print("Expected primary_language: Python")
    print(f"Observed primary_language: {primary}")

    if primary != "Python":
        print("\nBUG REPRODUCED: vendored/build files outvoted the real source files.")
    else:
        print("\nNot reproduced -- primary_language matched the expected value.")


if __name__ == "__main__":
    main()
