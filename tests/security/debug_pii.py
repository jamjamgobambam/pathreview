from safety.pii_scrubber import PIIScrubber

s = PIIScrubber()
text = """
Professional Background:
I worked at TechCorp for 5 years developing Python applications.
Email: john.smith@company.com
Phone: (555)-123-4567
SSN: 123-45-6789
I'm skilled in AWS and Kubernetes deployment.
"""
print("Original:\n", text)
print("Detected:")
for d in s.detect(text):
    print(d)
print("\nScrubbed:\n", s.scrub(text))
