## Solution plan

**Issue:** [Add a content hash to detect unchanged documents and skip re-embedding](https://github.com/ascherj/pathreview/issues/13)

### Understand
Currently, the `IngestionPipeline` in `pipeline.py` has two functions with placeholder code: `_check_skip` and 
`_record_ingested_source`. 

`_check_skip` is supposed to check if a source has already been ingested. If it has already been ingested,
then it is skipped. If it hasn't, then the pipeline should proceed and embed the source.

`_record_ingested_source` is supposed to keep track of the sources that have already been ingested. How? By assigning a
unique ID (using a hash) and inserting a record in the database. 

Since these functions have placeholder code, there is no way to check if a README.md file has been submitted twice 
without any changes.

The expected behavior is for the `IngestionPipeline` to detect unchanged documents, with the help of these two
functions, and to skip README.md files that have been submitted more than once without any changes.

### Map
I'll work in `pipeline.py`. In this file, I'll implement the missing logic in `_check_skip` and 
`_record_ingested_source`. I will also update the signature of both functions, so I'll have to update any calls.

The `IngestedSource` model already includes a field to store the `content_hash`, so I don't have any planned updates here.

### Plan
#### Fix `_record_ingested_source`
My first step will be to fix this function. To start with, I'll update the function signature so that it also
expects to receive source content's hash.

After that, I'll implement the database insertion. Once this has been implemented, I'll have a function that
correctly stores ingested sources in the database.

#### Fix `_check_skip`
My second step will be to implement the logic in this function. I'll update this function's signature as well so that 
it expects to receive the source content's hash.

After that, I'll implement the query-and-check logic. This logic will: query for matching `profile_id` + `source_type` 
records. If no matching records are found, then the function returns `None` and signals the pipeline to proceed with the 
embedding. If a matching record is found, the matching record's hash is compared to the incoming file's hash. If the hash
is the same, it means the file has been previously ingested and there are no changes so it should be skipped. If the 
hash is not the same, then the function returns `None` and signals the pipeline to proceed with the embedding.

#### Update the functions calls
Finally, any call to these functions will be updated. After this update, `ingest_readme` will be handling unchanged 
documents correctly.

#### Tests
To confirm that this solution is working, I'll run the tests I wrote to reproduce the behavior. If all the tests pass,
it means the fix correctly addressed this issue.

### Inputs & outputs

#### `_check_skip`
**Inputs:** source_id, profile_id, source_type, and content_hash

Using the inputs it checks for a profile_id + source_type match in the ingested sources history.
If a match is found, then the stored content hash and the incoming content hash are compared. If they are the same,
it means the incoming file has already been ingested before. If they don't match, the file is new.

For previously ingested sources, the function will return an `IngestResult` object that signals the 
pipeline to skip the source.

For new sources, the function will return `None`, which will signal the pipeline to proceed with the ingestion 
process for the source.

#### `_record_ingested_source`
**Inputs:** source_id, source_type, profile_id, chunk_count, content_hash, filename

The function inserts a new record in the database that represents an ingested source. 

It doesn't return any value, but can raise an `Exception` if it failed to save the ingested source.


### Risks & unknowns
Right now, the ingestion pipeline is not implemented in the project. Once implemented, new issues / bugs could come up.

### Edge cases
* Unchanged README.md files submitted more than once -> skip
* Same README.md content but different profile_id -> must not skip