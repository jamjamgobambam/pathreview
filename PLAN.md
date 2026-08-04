## Solution plan

**Issue:** DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings; link to issue: https://github.com/ascherj/pathreview/issues/80

### Understand
When a user's profile is deleted from the database, details about reviews associated with that profile are deleted as well, but embeddings in Chroma DB are left orphaned. The reviews and ingested sources are removed from Postgres, but embeddings created for a profile remain even after profile deletion in the vector database.

Actual behavior: Deleting a profile removes all associated information from Postgres, but it doesn't touch the embeddings in ChromaDB which exist indefinitely leading to wasted memory and slower retrieval time.

Expected behavior: All reviews, ingested sources, embeddings associated with a profile id should be deleted once a user's profile is deleted. 


### Map
- Files involved: `vector_store.py` and `profile_service.py`. In `vector_store.py` there's a function called `delete_by_source_id` which deletes a single ingested source's chunks, but because every user profile is defined as a collection, deleting sources doesn't delete a profile. There isn't a method to delete a collection, so the embeddings still remain even after a profile is deleted from Postgres. `profile_service.py` has a function called `delete_profile` but it deletes a profile associated with a profile id and its ingested sources from Postgres only, and so never ends up touching the vector database. I expect to update `vector_store.py` and `profile_service.py` so that the embeddings are also deleted when a profile is deleted.


### Plan

1. A `delete_collection` method needs to be created in `vector_store.py` that will delete the entire profile collection. It takes `collection_name: str` (consistent with the other methods like `delete_by_source_id` and `add_chunks`), so the caller is responsible for building the `profile_{profile_id}` name. Import statement needs to be added: `from chromadb.errors import NotFoundError` to catch the NotFoundError specifically for a profile collection that doesn't exist.
2. `delete_collection` needs to be called from `delete_profile` in `profile_service.py`, which builds the `profile_{profile_id}` collection name and passes it in to delete the embeddings. Import statement needs to be added: `from rag.retriever.vector_store import VectorStore`. An instance of a `VectorStore` needs to be created in the `delete_profile` method in `profile_service.py`. After which, `delete_collection` needs to be called on that instance to delete the profile collection with the specific profile id. Both statements are wrapped inside try/else to catch if deletion failed.
3. To test it, I'll create a profile, delete it, and then confirm via tests if the entire collection was deleted or not. 

### Inputs & outputs
The fix takes profile_id as an input at the `delete_profile` layer in order to delete the profile based on the associated id. `delete_profile` translates this into the `profile_{profile_id}` collection name and passes that `collection_name` to `delete_collection`. The fix should remove the profile from ChromaDB. 

### Risks & unknowns

The Postgres and ChromaDB deletes aren't one transaction, so if one succeeds and the other fails there will be half deleted data. Another risk is that if the collection name doesn't match `profile_{profile_id}` then nothing gets deleted. Since `delete_collection` now takes `collection_name` and `delete_profile` builds it, the naming convention must stay in sync with wherever collections are created (in `add_chunks`'s callers) — ideally the `profile_{profile_id}` string is constructed in one place. I'm also unsure which ChromaDB the app actually writes to (local `.chromadb` folder vs. the server at `http://localhost:8001`).

### Edge cases
An edge case could be deleting a profile that has no embeddings shouldn't crash because ChromaDB errors on a missing collection, so I'll use try/except. A profile that isn't found or isn't owned by the user is already handled by `delete_profile` returning `False`.