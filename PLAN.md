## Solution plan

**Issue:** Add snapshot tests for prompt templates to catch accidental changes (https://github.com/ascherj/pathreview/issues/37)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

We want anyone who is working on the codebase and makes changes to the prompt templates to update the templates' versions. This way, there is a convention that will allow others to trace changes in AI output quality. Currently, the prompt template tests barely or don't show these changes at all. So, a unit test needs to be added to only pass if a change is made while also having a version update (aside from when no changes are made and no version is updated).

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

tests and rag modules are the primary involved parties. scripts also becomes an involved party.
Specifically:
- tests/unit/test_prompt_templates.py
- rag/generator/prompt_templates.py
- scripts/

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. mkdir snapshots in tests/unit and commit a generated prompt_templates.json inside snapshots. Inside, there will be maps between each template and their (version, hash) of the template strings should be stored. For example:
{
  "skills_feedback": { "v1": "3f2a…" },
  "projects_feedback": { "v1": "9b1c…" },
  "first_impression":  { "v1": "7d4e…" }
}
This will be generated it once by running the script I will make in the 4th step later.
2. Add a snapshot_hashes() function to prompt_templates.py. This will generate hashes for all the text in the templates. This new function should be imported by both the test and the script in step 4.
3. Make a test that first checks if the instance of the snapshot even exists. If it doesn't, run the script to generate it (scripts/update_prompt_snapshot.py)
4. Make the regenerate script in scripts/update_prompt_snapshot.py. Compute the hashes of each version by using the imported hash function and write it to tests/unit/snapshots/prompt_templates.json.
5. In the test: If the instance of a snapshot already exists, go through each version of each template and hash their strings. Compare the hashes between the current prompt templates and those of the snapshot: 
If a version does not exist, pass with a non-fatal message saying that the version is not yet captured in a snapshot. Run the script to record it.
If a version already exists in the snapshot, compare the hashes between the current and the snapshot. If they differ, add a tuple with the version and template to a "failure" list. Continue scanning for more mismatches. Then, return a failure message that mentions all the template versions in the failure list.
6. Have this new test replace this unit test in test_prompt_templates.py: test_template_snapshot_content_hash(). This is both because its docstrings are not matching current implementation and it only checking for any change regardless of version bump seems to be an outdated requirement. We care about version bump. Now, generate a snapshot once by running the script.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

It uses what is already present (current rag/generator/prompt_templates.py templates and versions) as its inputs/check material. Then, it returns a pass/fail as a verification of if silent-edits were made to any template version without bumping the version.

### Risks & unknowns
What could go wrong? What are you still unsure about?

Committed snapshot could be regenerated within the same PR, which could hide silent edits. But if at code review, the reviewer sees the hash values being different without a new version key in prompt_templates.json, the issue can be caught.

### Edge cases
What inputs or states should your fix handle gracefully?

If there is no snapshot file, a test should fail and guide the user to run the script to generate a snapshot. 
Deleting a whole template and version is out of scope.