import sys

from safety.bias_detector import BiasDetector

# Test phrasings that should be flagged as biased but currently are not
failing_cases = [
    "bootcamp graduates can't write production code",
    "bootcamp education lacks fundamentals",
    "young developers can't handle complex systems",
    "bootcamp developers can't handle production systems",
    "bootcamp programmers lack proper training",
    "young bootcamp graduates can't write code and immigrant developers lack fundamentals",
    "self-taught developers are not equal to university graduates",
    "developers from poor backgrounds can't afford proper tools",
]

print("=== BIAS DETECTOR REPRODUCTION CHECK ===")
all_passed = True

for text in failing_cases:
    is_biased, reason = BiasDetector.detect_bias(text)
    print(f'Text:   "{text}"')
    print(f'Result: is_biased={is_biased}, reason="{reason}" (Expected: is_biased=True)')

    if not is_biased:
        print("❌ FAILED TO DETECT BIAS")
        all_passed = False
    else:
        print("✅ DETECTED")
    print("-" * 50)

if all_passed:
    print("SUCCESS: All biased phrasing was successfully detected.")
    sys.exit(0)
else:
    print("FAILURE: Some biased phrasings were missed due to narrow patterns.")
    sys.exit(1)
