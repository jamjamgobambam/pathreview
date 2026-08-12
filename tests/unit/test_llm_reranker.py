from typing import Any
from unittest.mock import Mock

from rag.retriever.llm_reranker import LLMReranker


def test_rerank_sorts_chunks_by_llm_score() -> None:
    # 1. Create fake chunks with their original scores
    chunks = [
        {"id": "chunk_1", "text": "Something irrelevant", "score": 0.9},
        {"id": "chunk_2", "text": "The perfect answer", "score": 0.4},
    ]

    # 2. Set up the reranker
    reranker = LLMReranker(api_key="fake_key", base_url="fake_url")

    # 3. Create a fake OpenAI client that returns "10" for chunk_2 and "2" for chunk_1
    mock_client = Mock()

    # We define a function that will be called whenever our code tries to use OpenAI
    def mock_create(*args: Any, **kwargs: Any) -> Mock:
        messages = kwargs.get("messages", [])
        prompt = messages[1]["content"]  # The user prompt is the second message

        # Create the fake nested response objects
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()

        # Check what the prompt contains to give the right score
        if "irrelevant" in prompt:
            mock_message.content = "2"
        elif "perfect answer" in prompt:
            mock_message.content = "10"

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        return mock_response

    # Tell the mock client to use our custom function
    mock_client.chat.completions.create.side_effect = mock_create

    # Replace the real OpenAI client with our fake one
    reranker.client = mock_client

    # 4. Run the reranker
    results = reranker.rerank("What is the answer?", chunks)

    # 5. Assert that the chunks were re-sorted!
    # Even though chunk_2 had a lower original score, the LLM should give it a 10,
    # so it should now be the first item in the results.
    assert results[0]["id"] == "chunk_2"
    assert results[1]["id"] == "chunk_1"
