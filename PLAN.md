## Understand

Issue #71 asks for a dedicated red-teaming test suite for the prompt injection defense.

The project already has prompt injection protection in `safety/prompt_defense.py`. This file contains the `PromptDefense` class, the `INJECTION_PATTERNS` collection, and the `sanitize()` and `is_injection_attempt()` methods.

The project also already has `tests/unit/test_prompt_defense.py`, which contains 32 unit tests for existing prompt injection patterns and sanitization behavior. I also inspected `tests/conftest.py`, which currently contains resume and README fixtures, but no prompt injection fixtures.

The main missing functionality is the dedicated security test file and reusable attack fixture directory requested by Issue #71:

- `tests/security/test_prompt_injection.py`
- `tests/fixtures/injection_attempts/`

I confirmed locally that neither path currently exists.

I ran the existing prompt defense unit tests and received 31 passing tests and one failing test. The failing test was `test_whitespace_variations_detected`, which relates to the current regular expression not detecting spaces before a colon, such as `System  :`. That existing failure appears separate from the requested red-team test suite, so it is outside the main scope of Issue #71.


## Map

The prompt injection defense is located in `safety/prompt_defense.py`.

Inside that file, the main code connected to Issue #71 is:

- `PromptDefense`, the class that handles prompt injection protection.
- `INJECTION_PATTERNS`, the regular-expression patterns used to detect suspicious text.
- `is_injection_attempt()`, which checks whether an input contains a prompt injection attempt.
- `sanitize()`, which removes or replaces detected injection content.

The current unit tests are located in `tests/unit/test_prompt_defense.py`. These tests check individual prompt injection patterns and sanitization behavior.

Shared pytest fixtures are located in `tests/conftest.py`, but this file currently contains only resume and README fixtures. It does not contain reusable prompt injection fixtures.

The new red-team test coverage should be added in:

- `tests/security/test_prompt_injection.py`
- `tests/fixtures/injection_attempts/`

The new security tests will use the existing `PromptDefense` methods and reusable fixture data to test a wider range of malicious, obfuscated, and benign inputs.


## Plan

To implement Issue #71, I plan to complete the following steps:

1. Review the existing prompt defense implementation and unit tests again to fully understand the current testing style and coding conventions used throughout the project.

2. Create the new security test file `tests/security/test_prompt_injection.py` by following the same layout, structure, naming conventions, and pytest style used in the existing test files. My goal is to make my contribution consistent with the rest of the codebase rather than generating a completely different testing style.

3. Create the `tests/fixtures/injection_attempts/` directory and organize reusable prompt injection examples that can be shared across multiple security tests.

4. Write red-team test cases for role switching, instruction override attempts, template injection, separator-based attacks, obfuscated formatting, combined attacks, and benign prompts that should not be flagged.

5. Run the project's unit tests and security tests to verify the new test suite works correctly and does not break the existing prompt defense behavior.


## Inputs & Outputs

### Inputs

The new test suite will use prompt injection examples as input, including known attack patterns, role-switching attempts, template injection, instruction override attempts, and normal user prompts. The tests will call the existing `PromptDefense.is_injection_attempt()` and `PromptDefense.sanitize()` methods without changing their public interfaces.

### Outputs

The expected output is a dedicated security test suite that verifies malicious prompt injection attempts are detected while legitimate prompts continue to be accepted. The reusable fixture directory should make it easier to expand security testing in the future while keeping the tests organized and consistent with the rest of the project.


## Risks & Unknowns

One risk is creating tests that duplicate the existing unit tests instead of adding meaningful red-team coverage. Before writing new tests, I will compare them with `tests/unit/test_prompt_defense.py` to avoid unnecessary duplication.

Another risk is creating false positives by treating legitimate user prompts as malicious prompt injection attempts. The new security tests should include both malicious and benign examples to verify the defense behaves correctly.

I also need to determine what prompt injection examples should be included in the reusable fixture directory. I plan to review the existing prompt injection patterns and organize realistic attack examples that match the project's current implementation.

The existing failure in `test_whitespace_variations_detected` is another unknown. Some new red-team examples may expose the same limitation in `PromptDefense.INJECTION_PATTERNS`. If that happens, I will document the failure clearly and determine whether updating the detection logic is required by Issue #71 or should be handled separately.

Finally, I want to make sure my new tests follow the same project structure, naming conventions, and pytest style as the existing test files so the contribution is consistent with the rest of the codebase.



## Edge Cases

The new red-team test suite should verify that the prompt defense handles both normal and unusual inputs correctly. Some important edge cases include:

- Legitimate prompts that mention words such as "system" or "assistant" in a normal sentence without being treated as prompt injection.
- Prompt injection attempts that contain extra whitespace or formatting variations, such as spaces before a colon or multiple blank lines.
- Inputs that combine several attack techniques in the same prompt, such as role switching, template injection, and instruction override attempts.
- Empty strings or whitespace-only input to confirm the detection methods do not fail or incorrectly classify them as attacks.
- Very long prompts that contain malicious instructions near the end of the input to verify the detection logic continues to work correctly.
- Prompt injection attempts that use different capitalization, such as `SYSTEM:`, `system:`, or `Assistant:`, to verify detection remains case-insensitive.