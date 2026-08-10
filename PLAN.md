\# Solution plan



\*\*Issue:\*\* Bias detector patterns are too narrow to match common phrasings

Issue link: https://github.com/ascherj/pathreview/issues/151



\## Understand



The root cause of this issue is that the educational bias detector in `safety/bias\_detector.py` uses regular-expression patterns that only recognize a limited set of educational bias statements. Common statements about bootcamp graduates, self-taught developers, and online-course students are not consistently detected. The expected behavior is for these common variations to be recognized while preserving the detector's existing behavior.



\## Map



Files involved:



\* `safety/bias\_detector.py` – contains the educational bias detection patterns.

\* `tests/unit/test\_bias\_detector.py` – contains the unit tests that verify the detector's behavior.



\## Plan



1\. Review the existing regex patterns in `safety/bias\_detector.py`.

2\. Identify common educational bias statements that are currently not detected.

3\. Expand the regex patterns to recognize these additional phrasings without creating overly broad matches.

4\. Add regression tests to `tests/unit/test\_bias\_detector.py` for the newly supported examples.

5\. Run Ruff, Black, mypy, and the unit tests to ensure the changes do not introduce regressions.



\## Inputs \& outputs



\*\*Inputs\*\*



\* User-generated text that is analyzed for educational bias.



\*\*Outputs\*\*



\* The detector correctly identifies additional educational bias statements that were previously missed while continuing to recognize existing supported patterns.



\## Risks \& unknowns



\* Regex patterns may become too broad and incorrectly flag neutral statements.

\* Changes could unintentionally affect existing educational bias detection behavior.

\* Additional edge cases may appear during testing that require refining the regex patterns.



\## Edge cases



\* Different wording that expresses the same educational bias.

\* Uppercase and lowercase variations.

\* Statements containing punctuation.

\* Neutral discussions of educational backgrounds should not be flagged as biased.



