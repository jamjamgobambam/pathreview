## Summary

<!-- One paragraph describing what this PR does and why -->

The `bias_detector` takes text as input and evaluates whether the text contains bias. Initially, the `bias_detector` was only able to detect bias if the text followed the exact keyword pattern. However, it could not detect phrases with a similar meaning, such as "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education," instead of "bootcamp graduates lack rigor." This PR resolves the issue by changing the implementation logic. Instead of performing an exact pattern check, it uses lists of educational and demographic subjects and negative predicates to check for co-occurrence and determine whether text is biased.

## Issue

Closes #151

## Changes

<!-- Bullet list of the specific changes made -->

- Created three lists in `bias_detector.py`—`EDUCATIONAL_SUBJECTS`, `DEMOGRAPHIC_SUBJECTS`, and `NEGATIVE_PREDICATES`—filled with distinct keywords for each list.
- Created the `has_demographic_subject`, `has_educational_subject`, and `has_negative_predicate` Boolean values to check whether the text contains any subjects or keywords from each list.
- Used the Boolean values for evaluation. If `has_demographic_subject` is `True` and `has_negative_predicate` is `True`, or if `has_educational_subject` is `True` and `has_negative_predicate` is `True`, the warning is logged and the function returns that bias was detected.
- Added five more test cases to `tests/test_bias_detector.py`:
  - `test_co_occurrence_does_not_depend_on_word_order`: Tests whether the bias detector can detect bias without the exact word order—for example, when a negative predicate appears before the educational subject.
  - `test_single_signal_without_co_occurrence_not_flagged`: Tests that text containing only a subject or only a negative predicate is not flagged as biased, preventing false positives.
  - `test_demographic_category_takes_precedence_when_both_match`: Tests that, when both subject categories (educational and demographic) appear, the demographic category takes precedence in bias detection.
  - `test_detected_bias_emits_monitoring_warning`: Tests that the bias detector emits monitoring-event warnings when it detects bias.
  - `test_unbiased_feedback_does_not_emit_monitoring_warning`: Tests that the bias detector does not trigger an alert when it does not detect bias in the text.

## Testing

<!-- How did you verify your changes? -->

- [x] Unit tests pass (`make test-unit`)—see Notes for Reviewers for reference.
- [ ] Integration tests pass (`make test-integration`).
- [ ] Linter passes (`make lint`).
- [ ] Type checker passes (`make typecheck`).
- [x] New/updated tests cover the changes—see Notes for Reviewers for reference.

## Screenshots / Demo

<!-- If applicable, add screenshots or a link to a demo video -->

Not applicable, as this is a backend logic change.

## Notes for Reviewers

<!-- Anything the reviewer should pay particular attention to -->

**Unit test cases pass:**

Before the implementation, there were already test-case failures unrelated to the narrow pattern-checking issue. I was able to run Ruff, mypy, and pytest checks on the specific test suites for `bias_detector`, and all 40 test cases passed successfully.

**New test cases:**

- More test cases were added to `test_bias_detector.py` to check whether the `bias_detector` can function and process successfully.
