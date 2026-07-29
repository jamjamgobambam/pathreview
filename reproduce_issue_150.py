"""
Reproduction for issue #150: Tech detector counts vendored and
build-output files, skewing language detection.

A repo with 2 Python source files and 6 vendored/bundled JS files
is incorrectly reported as primarily JavaScript, because
tech_detector.py does not exclude node_modules/ or build/ paths.

Expected: 'Python'
Observed: 'JavaScript'
"""

from agent.tools.tech_detector import TechDetector

t = TechDetector()
files = [
    "main.py",
    "core/app.py",
    "node_modules/lib/index.js",
    "node_modules/lib/util.js",
    "node_modules/x/a.js",
    "node_modules/y/b.js",
    "build/bundle.js",
    "build/vendor.js",
]
result = t.execute({"files": files}).data["primary_language"]
print(f"primary_language = {result}")
assert result == "Python", f"BUG REPRODUCED: expected 'Python', got '{result}'"
