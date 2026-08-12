"""
Reproduction for issue #34: no LLM re-ranking step exists.

HybridRetriever.retrieve() ranks chunks purely by blended
vector_score + keyword_score. A chunk can pass min_score and
land in the top-k results while being semantically irrelevant
to the query -- there's no step that checks actual relevance.

This is a structural gap, not a runtime exception: the gap is
demonstrated by inspecting retrieve()'s logic, not a stack trace.
"""

# Confirmed via rag/retriever/hybrid.py:
# - HybridRetriever.retrieve() blends vector_score and keyword_score only
# - min_score (default 0.3) is a numeric threshold, not a relevance check
# - results.sort(key=lambda x: x["score"], reverse=True) -- no LLM/semantic
#   scoring step exists anywhere in the retrieval path
# - No reranker.py module exists in rag/retriever/

# Example: a chunk with high keyword overlap (e.g. shares rare terms
# with the query) but is topically unrelated can still score above
# min_score and reach the generator, since keyword_score doesn't
# capture semantic relevance.

print("Confirmed: HybridRetriever.retrieve() has no LLM re-ranking step.")
print("See rag/retriever/hybrid.py -- blended scoring only, no reranker.py exists.")
