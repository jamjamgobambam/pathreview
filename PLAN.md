## Solution plan

**Issue:** [Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

### Understand
The root cause of this issue is the _check_skip method in /ingestion/pipeline.py. When querying the database for an existing source, it doesn't utilize the source_type parameter passed into the function, and only uses the source_id. Additionally, source_id is not a keyword argument for IngestedSource, so querying using source_id=source_id would result in an invalid argument error. 
The expected behavior is that GitHub ingestion would be skipped if it was previously ingested. The actual behavior is that evidence of the existing GitHub that was ingested previously is not found with the current query, and so a duplicate embedding is generated and stored in the vector database. 

### Map
The relevant files are ingestion/pipeline.py and core/models/ingested_source.py.
The relevant function are _check_skip(source_id, source_type) and the functions that reference _check_skip() (ingest_resume, ingest_readme, ingest_repo_metadata).

### Plan
1. Make sure that the query is matching the source_id parameter to the content_hash attribute in the IngestedSource table.
2. Make sure that the query is including the source_type parameter, matching it to the source_type attribute in the IngestedSource table.
3. Generate a test suite or manually test to confirm that duplicate GitHub entries are no longer stored in the vector database.

### Inputs & outputs
**Input:**
- `source_id` (content hash from `_hash_content()`)
- `source_type` (resume, readme, repo, web)
- `profile_id` (UUID of the profile owner)

**Output:**
- `_check_skip()` returns an `IngestResult` if source exists (skip=True), or None to proceed
- `_record_ingested_source()` creates an actual `IngestedSource` database record with content_hash, source_type, profile_id, and chunk_count
- Vector DB remains clean without duplicate embeddings

### Risks & unknowns
**Risks:**
- If duplicates already exist in production, this only prevents future duplicates; cleanup may be needed
- Query must include all three fields (content_hash, source_type, profile_id) to avoid false positives

**Unknowns:**
- Are there existing duplicate embeddings in ChromaDB that need cleanup?
- Should we add a migration to detect and remove existing duplicates?
- What happens if the same content is legitimately ingested for multiple profiles?

### Edge cases
- **Same content, different source_type**: Should NOT be considered a duplicate (e.g., repo content extracted as both README and full repo)
- **Same content, different profile_id**: Should NOT be considered a duplicate (different users uploading same repo)
- **Partial updates**: If resume content changes slightly (header/footer), new content_hash generated, treated as new (expected behavior)
- **Null/missing profile_id**: Should fail gracefully rather than creating orphaned records
- **Database unavailable**: `_check_skip()` catches exceptions and logs warning, allows ingestion to proceed (current behavior acceptable)
- **Concurrent ingestions**: Same source ingested twice simultaneously could create race condition if not using database constraints
