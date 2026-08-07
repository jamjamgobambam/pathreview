## Solution plan

**Issue Title:** README scorer test fixture is too short for its own word-count assertion #156

**Issue Link:** https://github.com/ascherj/pathreview/issues/156


### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
The Root Cause of this Issue is that the Sample README used in the [test_readme_with_all_quality_signals] Test Fixture, only contains around ~51 Words, while the Test expected it to be much higher than that, higher than a 100 Words. Because of this, the Assertion Fails even though the [ReadmeScorer] Correctly counts the Words. The Expected Behavior is for the Test Fixture and its Assertions to match each other so that the Tests can accurately Validates the Scorer, but the Actual Behavior as of now is shows that the Text Fixture and its Assertion doesn’t match each other, thereby creating the Issue in the first place.


### Map
<!-- Which files, functions, or modules are involved? List the specific files you expect to touch. -->
[**Files expected to Touch**]
- tests/unit/test_readme_scorer.py

[**Files / Functions / Modules**]
- def test_readme_with_all_quality_signals(self, scorer)

### Plan
<!-- What are the steps to fix this issue? Break it into 3–5 concrete sub-tasks. -->
1) First to Review the Test Fixture Failure and Determine whether to Extend the Fixture or Correct the Assertion so that the Test Validates to what it intends to.
2) Then Compare the Fixture’s Word Count with the Expected Thresholds that is used by the [ReadmeScorer].
3) After that, we made Changes to the README Fixture or the Assertion so that the Test Validates to its Intended Behavior.
4) Finally, Run the Test once more to Verify that No Tests Fail and the Issue is Fixed.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
The Fix Take Input would be the Sample README Data used by [test_readme_with_all_quality_signals] that is used by the Unit Test. It should then Produce that the Unit Test passes because the README Fixture matches the expected conditions, allowing the [ReadmeScorer] to be validated correctly.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
Trying to Update the Fixture so that the Test Reflects its Intended Behavior, could probably require Multiple Assertions to happen and such. Also trying to Update the Assertion could lead to other Problems down the Line. There could also be where the Word Count could be Exactly 100.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
The README can contain things like a Markdown Syntax that Affects the Word Count. When Adding changes to the Fixture or Assertion, it would allow all Tests to Passed. The Intended Fix should also be Consistent with the Labeled Categories and such.

---