from safety.bias_detector import BiasDetector

result = BiasDetector.detect_bias(
    "The candidate only attended a bootcamp, so this project lacks the "
    "rigor of a formal CS education"
)
print("Bootcamp phrasing:", result)

result2 = BiasDetector.detect_bias(
    "Given their age, they likely cannot keep up with modern frameworks"
)
print("Age phrasing:", result2)
