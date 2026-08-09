## Solution plan

**Issue:** [issue title and link]
DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings
 #80
 https://github.com/ascherj/pathreview/issues/80

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause of the issue is that when a profile is deleted, nothing is done to get rid of the vector store embeddings associated with the deleted profile. They're expected to be deleted but actually, they're not.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
core/services/profile_service.py has lots of the underlying logic in the deletion of a profile, so I would likely add to that, and rag/retriever/vector_store.py has the function delete_by_source_id, which will undoubtedly be useful
### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1) Find out how to retrieve the source_ids of the vector store embeddings associated with the profile to be deleted. Alternatively find a better way to delete them
2) Call the function delete_by_source_id in profile_service.py to get rid of all these vector store embeddings
3) Check my work

### Inputs & outputs
What does your fix take as input? What should it produce or change?
It should take the source_ids associated with the profile to be deleted and then delete them
### Risks & unknowns
What could go wrong? What are you still unsure about?
I still don't fully grasp pathreview, and it may be difficult grabbing the source_id of everything I want to delete, maybe there is a better way
### Edge cases
What inputs or states should your fix handle gracefully?
Make sure I don't delete the vector store embeddings of a profile that doesn't exist.