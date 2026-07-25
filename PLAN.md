## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/146

### Understand

The scrubber is supposed to hide secure information like phone numbers, SSN, private information, etc. The issue was that some formats were ignored, which allowed secure information to leak. This included numbers not following the 111-111-1111 format for certain formats being mistaken for addresses.

### Map

I will have to look into `pii_scrubber.py` where the logic lives.
While there, I will look into the `PIIScrubber().scrub()` function to see how the system is detecting the format, which is by `reg` using the `PII_PATTERNS` dictionary.

### Plan
I will just create simple test cases


* Create my own pytest function named `test_pii_my_take()` inside `test_pii_scrubber.py`.
* Create test doc string with made up numbers.
* Print the after math.

### Inputs & outputs

See what inputed data is being redated and what is passing the scrubber. 

### Risks & unknowns

If a real location falls outside the normal format in the hardcoded reg, it may pass the redated test.

### Edge cases

Empty string

The empty string itself won't cause an error, but for performance it's best to just leave the function early.