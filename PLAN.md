## Solution plan

**Issue:** [Add a content hash to detect unchanged documents and skip re-embedding - https://github.com/ascherj/pathreview/issues/13]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
This feature is not yet wired in the application. The check_skip method, the source_id and the ingest_readme are all there but check_skip does nothing right now. I will implement this method as part of my solution. Right now, the README is ingested everytime the user uploads their repo. If this is a re-upload of the same repo, than the README is most likely not changed which is an oversight since ingesting the readme is an expensive API call. I will work to conditiionally ingest the readme, ONLY if it has been changed.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
I need to work on the pipeline.py file and touch the _check_skip function and the ingest_reame function. I would also need to create a file: test_ingestion_pipeline.py and create a couple functions to test this feature.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
- Create tests to recreate the readme ingestion for ease of testing. This should test all cases where the README changes and when it does not, otherwise ingest_readme should function the same.
-Implement the check_skip function for README files. This should involve an if statement or two and a db query.
-Ensure _check_skip function is working by testing db query directly.
-Run unit tests again and ensure feature works as intended

### Inputs & outputs
What does your fix take as input? What should it produce or change?
My fix takes in the README file contents,  the repository name and the profile id. When I implement my fix, if the re-ingested readme is the same as the original one then it should return:
IngestResult(
                    source_id=source_id,
                    chunk_count=0,
                    skipped=True,
                    skip_reason="Source already ingested",
                )
Otherwise, it should return:
IngestResult(
                source_id=source_id,
                chunk_count=len(chunks),
                skipped=False,
)

### Risks & unknowns
What could go wrong? What are you still unsure about?
The functionality of the ingest_readme function could change in a way not intended. Ex: Skipping ingesting readmes entirely. The DB query can return an error or come back with an unexpected result. I will test these outcomes throughouly

### Edge cases
What inputs or states should your fix handle gracefully?
Some edge cases may be the str or bytes implementation should hash identically for the same text. An empty or blank readme should also be considered identical