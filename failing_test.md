[root@adiLegion pathreview]# .venv/bin/pytest tests/unit/test_tech_detector.py
============================================================== test session starts ===============================================================
platform linux -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /mnt/c/Users/adith/Codepath/pathreview
configfile: pyproject.toml
plugins: anyio-4.14.2, hypothesis-6.156.6, asyncio-1.4.0, benchmark-5.2.3, cov-7.1.0, pytest_httpserver-1.1.5
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 27 items                                                                                                                               

tests/unit/test_tech_detector.py ...F.F.....................                                                                               [100%]

==================================================================== FAILURES ====================================================================
__________________________________________________ TestTechDetector.test_node_modules_excluded ___________________________________________________

self = <tests.unit.test_tech_detector.TestTechDetector object at 0x77438f9eec40>
detector = <agent.tools.tech_detector.TechDetector object at 0x77438f9ee9e0>

    def test_node_modules_excluded(self, detector):
        """Test node_modules/ directory is excluded from counts."""
        files = [
            "src/main.py",
            "node_modules/package1/index.js",
            "node_modules/package2/lib.js",
            "utils.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
>       assert data["primary_language"] == "Python"
E       AssertionError: assert 'JavaScript' == 'Python'
E
E         - Python
E         + JavaScript

tests/unit/test_tech_detector.py:78: AssertionError
-------------------------------------------------------------- Captured stdout call --------------------------------------------------------------
2026-07-14 21:51:21 [info     ] tech_detected                  frameworks_count=0 languages_count=2 primary_lang=JavaScript
_________________________________________________ TestTechDetector.test_build_directory_excluded _________________________________________________

self = <tests.unit.test_tech_detector.TestTechDetector object at 0x77438fa619d0>
detector = <agent.tools.tech_detector.TechDetector object at 0x77438f9eb650>

    def test_build_directory_excluded(self, detector):
        """Test build directory is excluded."""
        files = [
            "src/main.py",
            "build/generated.js",
            "build/bundle.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
>       assert data["primary_language"] == "Python"
E       AssertionError: assert 'JavaScript' == 'Python'
E
E         - Python
E         + JavaScript

tests/unit/test_tech_detector.py:105: AssertionError
-------------------------------------------------------------- Captured stdout call --------------------------------------------------------------
2026-07-14 21:51:22 [info     ] tech_detected                  frameworks_count=0 languages_count=2 primary_lang=JavaScript
============================================================ short test summary info =============================================================
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded - AssertionError: assert 'JavaScript' == 'Python'
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded - AssertionError: assert 'JavaScript' == 'Python'        
========================================================== 2 failed, 25 passed in 2.61s ==========================================================