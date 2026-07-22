## Solution plan

**Issue:** Resume section detection fails on text with leading whitespace - https://github.com/ascherj/pathreview/issues/147

### Understand

The root cause is in `ResumeParser._detect_sections`. Its regex patterns look for known section headers at the start of a line, but they do not allow leading spaces or tabs before the header text. Text extracted from PDFs commonly includes indentation, so input like `    Education:` or `\tSkills:` can fail section detection even though those are valid resume section headers.

Expected behavior: the parser should detect known section headers whether they start at column 0 or have leading whitespace. Actual behavior: indented section headers may be missed, causing `detected_sections` to be empty or incomplete.

Local reproduction:

```bash
python -c "from ingestion.parsers.resume_parser import ResumeParser; r=ResumeParser(); text='John Smith\n    Education:\n- B.S. Computer Science\n\tSkills:\nPython\n'; print(r.parse(text).metadata['detected_sections'])"
```

Observed output:

```text
[]
```

This confirms that the current parser misses valid section headers when those headers have leading spaces or tabs.

### Map

Files expected to touch:

- `ingestion/parsers/resume_parser.py` - update `_detect_sections` so its header regex allows optional leading whitespace before known section names.
- `tests/unit/test_resume_parser.py` - add a regression test covering leading spaces and tabs before section headers.

Relevant code:

- `ResumeParser.parse()` calls `_parse_markdown()` for string resumes and `_parse_pdf()` for PDF bytes.
- Both `_parse_markdown()` and `_parse_pdf()` call `_detect_sections()`.
- Existing parser tests already cover standard section detection in `test_detect_sections`.

### Plan

1. Add a failing regression test in `tests/unit/test_resume_parser.py` with resume text containing leading spaces and tabs before headers like `Education:`, `Skills:`, and `Experience:`.
2. Confirm the current parser misses at least one of those indented headers.
3. Update `_detect_sections` in `ingestion/parsers/resume_parser.py` so the regex patterns allow optional leading whitespace at the start of each line.
4. Keep the regex anchored to line starts with `^` and `re.MULTILINE` so it does not match section words in the middle of ordinary sentences.
5. Run the targeted resume parser tests, then run the broader unit tests if time allows.

### Inputs & outputs

Inputs:

- Resume text as a string or extracted PDF text.
- Known section header names from `SECTION_HEADERS`.
- Headers that may appear at the beginning of a line with leading spaces or tabs.

Outputs:

- `metadata["detected_sections"]` includes the expected section names for indented headers.
- Existing behavior still works for non-indented headers like `Experience:` and `Skills: Python`.
- The parser continues to avoid matching section words that appear in normal prose.

### Risks & unknowns

- The regex could become too broad if it is not kept anchored to the start of each line.
- The current function returns `list(set(detected))`, so detected section order is not stable; tests should check membership rather than exact list order.
- The issue mentions PDF extraction, but the simplest regression test can use string input because `_detect_sections` receives plain text from both Markdown and PDF parsing paths.
- There may already be open PRs linked to the issue, so the implementation should stay minimal and easy to compare.

### Edge cases

- Headers with spaces before them, such as `    Education:`.
- Headers with tabs before them, such as `\tSkills:`.
- Headers with no leading whitespace, such as `Experience:`.
- Headers without colons, such as a line containing only `Projects`.
- Non-header sentences that mention words like education, skills, or experience in the middle of a line.

<!--
PAUSED DUE TO MISSING FILES

Old Issue #105 plan, preserved for reference.

## Solution plan

**Issue:** Add accessibility tests for the review page using jest-axe - https://github.com/ascherj/pathreview/issues/105

### Understand

The issue is a frontend test coverage gap. `ReviewPage` exists and renders the portfolio review experience, but there are no automated accessibility tests for it. The project already has Vitest, React Testing Library, jsdom, and `jest-axe` listed in the frontend dependencies, but the existing setup does not register `toHaveNoViolations`, and there is no `frontend/src/pages/__tests__/ReviewPage.test.tsx`.

To reproduce the issue, I inspected the frontend test setup and searched for accessibility coverage. The search found `jest-axe` in `frontend/package.json`, but no `axe()` calls, no `toHaveNoViolations()` assertions, and no ReviewPage test file under `frontend/src/pages`. The expected behavior after the fix is that ReviewPage has automated jest-axe coverage following the existing Vitest and React Testing Library patterns.

### Map

Expected files to touch:

- `frontend/src/test/setup.ts` - register the `jest-axe` matcher with Vitest's `expect`.
- `frontend/src/pages/__tests__/ReviewPage.test.tsx` - add new ReviewPage accessibility tests.
- `frontend/src/components/ReviewSection.tsx` - only if the new accessibility test exposes a genuine ARIA/accessibility violation.
- `frontend/src/components/__tests__/ReviewSection.test.tsx` - only if a minimal production accessibility fix changes the component's collapsed/expanded test expectations.

Relevant existing files inspected:

- `frontend/src/pages/ReviewPage.tsx` - ReviewPage uses `useParams`, `useNavigate`, `useReviewStatus`, `apiClient.getReview`, and `ReviewSection`.
- `frontend/src/hooks/useReviewStatus.ts` - ReviewPage status polling dependency.
- `frontend/src/services/api.ts` - source of `apiClient.getReview`.
- `frontend/src/components/ReviewSection.tsx` - child component rendered by ReviewPage for review feedback sections.
- `frontend/src/components/__tests__/ReviewSection.test.tsx` - existing React Testing Library style and ARIA-related assertions.
- `frontend/src/components/__tests__/ProfileForm.test.tsx` - existing mocking style with Vitest.

### Plan

1. Configure `jest-axe` in the shared test setup by importing `toHaveNoViolations` and extending Vitest's `expect`.
2. Create `frontend/src/pages/__tests__/ReviewPage.test.tsx` with local mock review data and a small render helper using `MemoryRouter` and `Routes`.
3. Mock `useReviewStatus` so ReviewPage can be tested in polling, failed, and complete states without real timers or API polling.
4. Mock `apiClient.getReview` so the completed review state renders deterministic review content and feedback sections.
5. Add `axe(container)` assertions for the important ReviewPage states and verify the tests pass.
6. If axe reports a real violation, make the smallest possible production fix, likely in `ReviewSection`, then rerun the accessibility tests.

### Inputs & outputs

Inputs:

- A review ID from the route path `/reviews/:reviewId`.
- Mocked `useReviewStatus` return values for loading, failed, and complete review states.
- Mocked `apiClient.getReview` response data for a completed review.

Outputs:

- A new automated test file that verifies ReviewPage renders with no common accessibility violations.
- Shared test setup that supports `toHaveNoViolations`.
- Optional minimal production accessibility fix only if the new tests reveal a real issue.

### Risks & unknowns

- `ReviewSection` currently sets `aria-controls` on its accordion button, but the controlled content is only mounted when expanded. Axe may flag that if the controlled ID is absent while the section is collapsed.
- TypeScript may need a small Vitest matcher type adjustment for `toHaveNoViolations`.
- The full frontend suite should be run from the WSL environment because the local setup was installed there. Running it from Windows/PowerShell can fail due to platform-specific optional dependencies.
- Existing `ProfileForm.test.tsx` imports `@testing-library/user-event`, but that package was not listed in `frontend/package.json` during inspection; that may be an unrelated test-suite blocker if the full suite fails.

### Edge cases

- ReviewPage is still polling and displays the loading state.
- ReviewPage receives a failed review state and displays the failure message.
- Completed ReviewPage has no feedback sections.
- Completed ReviewPage has one or more collapsed feedback sections.
- A mocked API call for the full review rejects and the page displays a fetch error.
-->
