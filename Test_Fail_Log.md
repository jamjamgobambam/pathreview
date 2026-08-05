================================================================ FAILURES ================================================================
______________________________________ TestBiasDetector.test_dismissive_bootcamp_language_detected _______________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x10768d6d0>

    def test_dismissive_bootcamp_language_detected(self):
        """Test dismissive bootcamp language is detected as biased."""
        text = "bootcamp graduates can't write production code"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:18: AssertionError
__________________________________________ TestBiasDetector.test_bootcamp_lacks_rigor_detected ___________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107d95390>

    def test_bootcamp_lacks_rigor_detected(self):
        """Test 'bootcamp lacks rigor' language detected."""
        text = "bootcamp education lacks fundamentals"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:27: AssertionError
_______________________________________ TestBiasDetector.test_demographic_assumption_age_detected ________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107d97350>

    def test_demographic_assumption_age_detected(self):
        """Test demographic assumption about age detected."""
        text = "young developers can't handle complex systems"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:75: AssertionError
_____________________________________________ TestBiasDetector.test_coding_bootcamp_variant ______________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107db8ad0>

    def test_coding_bootcamp_variant(self):
        """Test 'coding bootcamp' variant is detected."""
        text = "coding bootcamp graduates can't write enterprise code"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:190: AssertionError
_______________________________________ TestBiasDetector.test_developer_vs_programmer_distinction ________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107daa350>

    def test_developer_vs_programmer_distinction(self):
        """Test both developer and programmer terms detected."""
        text_dev = "bootcamp developers can't handle production systems"
        text_prog = "bootcamp programmers lack proper training"
    
        is_biased_dev, _ = BiasDetector.detect_bias(text_dev)
        is_biased_prog, _ = BiasDetector.detect_bias(text_prog)
    
>       assert is_biased_dev is True
E       assert False is True

tests/unit/test_bias_detector.py:208: AssertionError
_____________________________________________ TestBiasDetector.test_multiple_bias_indicators _____________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107d977d0>

    def test_multiple_bias_indicators(self):
        """Test text with multiple bias indicators."""
        text = "young bootcamp graduates can't write code and immigrant developers lack fundamentals"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:217: AssertionError
____________________________________________ TestBiasDetector.test_negative_educational_claim ____________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107db8c10>

    def test_negative_educational_claim(self):
        """Test negative claims about education detected."""
        text = "self-taught developers are not equal to university graduates"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:225: AssertionError
_______________________________________________ TestBiasDetector.test_rich_poor_assumption _______________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107db9890>

    def test_rich_poor_assumption(self):
        """Test rich/poor background assumption detected."""
        text = "developers from poor backgrounds can't afford proper tools"
    
        is_biased, reason = BiasDetector.detect_bias(text)
    
>       assert is_biased is True
E       assert False is True

tests/unit/test_bias_detector.py:241: AssertionError
____________________________________________ TestBiasDetector.test_assumption_vs_observation _____________________________________________

self = <tests.unit.test_bias_detector.TestBiasDetector object at 0x107dba710>

    def test_assumption_vs_observation(self):
        """Test that observations are not flagged, assumptions are."""
        observation = "your resume shows bootcamp attendance"  # Factual
        assumption = "bootcamp attendance means inadequate training"  # Biased
    
        is_biased_obs, _ = BiasDetector.detect_bias(observation)
        is_biased_ass, _ = BiasDetector.detect_bias(assumption)
    
        assert is_biased_obs is False  # Factual
>       assert is_biased_ass is True  # Biased assumption
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       assert False is True

tests/unit/test_bias_detector.py:276: AssertionError
======================================================== short test summary info =========================================================
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_dismissive_bootcamp_language_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_bootcamp_lacks_rigor_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_demographic_assumption_age_detected - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_coding_bootcamp_variant - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_developer_vs_programmer_distinction - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_multiple_bias_indicators - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_negative_educational_claim - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_rich_poor_assumption - assert False is True
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_assumption_vs_observation - assert False is True
====================================================== 9 failed, 23 passed in 0.29s ======================================================