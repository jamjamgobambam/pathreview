\## Solution plan

\*\*Issue:\*\* Structural chunker silently drops documents with no headings (#149)



\### Understand

\_extract\_sections() only appends content once heading\_stack is non-empty.

Headingless docs never trigger that, so sections=\[] -> chunk()=\[] -> the

document is "ingested" with 0 chunks and no error surfaces anywhere.



\### Map

\- ingestion/chunking/structural\_chunker.py -- chunk(), the only file changed

\- ingestion/chunking/semantic\_chunker.py -- reused as-is for the fallback

\- tests/unit/test\_structural\_chunker.py -- test\_document\_with\_no\_headings

&#x20; already exists and is already failing; this is the acceptance test



\### Plan

1\. Reproduce: run the issue's snippet + the named pytest, confirm failure (done)

2\. In chunk(), after sections = self.\_extract\_sections(text): if not

&#x20;  sections, return self.semantic\_chunker.chunk(text, metadata)

3\. Re-run test\_structural\_chunker.py in full (confirm no regressions on

&#x20;  the nested-heading / large-section tests)

4\. make check \&\& make test-unit before opening the PR



\### Inputs \& outputs

Input: raw text + metadata dict. Output: list\[Chunk]. Via the fallback

path, chunks won't carry heading\_path/heading\_level -- confirmed safe,

since existing callers already guard those keys with .get()/"in".



\### Risks \& unknowns

\- pipeline.py never warns on a 0-chunk result -- out of scope to fix here,

&#x20; worth one line in the PR description so reviewers know it was noticed

\- Leading text before the first heading in docs that do have headings

&#x20; later is dropped by the same root cause -- separate bug, flag not fix



\### Edge cases

\- Whitespace-only input must still return \[] (don't regress that test)

\- Very large headingless doc must sub-split via semantic\_chunker, not

&#x20; return one oversized chunk

\- Very short headingless text must still return exactly 1 chunk

