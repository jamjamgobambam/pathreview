"""Reproduction for issue #150 — tech detector counts vendored/build files.

https://github.com/ascherj/pathreview/issues/150

Run:  python repro_issue_150.py

The `tech_detector` tool is supposed to ignore third-party / generated code
(node_modules/, build/, vendor/, ...) when guessing a repo's primary language.
Because the skip patterns in `TechDetector._should_skip_file` were written with
a leading slash ("/node_modules/", "/build/"), they only matched those
directories when nested inside another folder. Root-level vendored/build
directories (the normal case) have root-relative paths with no leading slash,
so nothing was excluded and the bundled JS outnumbered the real source.

Observed on pre-fix code (base commit 54cc749):
    primary_language: JavaScript      # 6 vendored .js files win over 2 .py files

    $ pytest tests/unit/test_tech_detector.py \
        -k "node_modules_excluded or build_directory_excluded"
    FAILED ... test_node_modules_excluded   - assert 'JavaScript' == 'Python'
    FAILED ... test_build_directory_excluded - assert 'JavaScript' == 'Python'
    2 failed, 25 deselected

Expected (and produced after the fix):
    primary_language: Python
"""

from agent.tools.tech_detector import TechDetector

# Exact input from the issue report: 2 real Python source files plus 6
# vendored/bundled JavaScript files under node_modules/ and build/.
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

EXPECTED = "Python"


def main() -> int:
    detector = TechDetector()
    result = detector.execute({"files": FILES})
    observed = result.data["primary_language"]

    print(f"expected primary_language: {EXPECTED}")
    print(f"observed primary_language: {observed}")

    if observed != EXPECTED:
        print("REPRODUCED: vendored/build files skewed language detection.")
        return 1

    print("OK: vendored/build files correctly excluded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
