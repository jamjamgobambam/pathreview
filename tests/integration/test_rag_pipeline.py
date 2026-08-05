"""Tests for the retrieval -> generation -> parsing RAG pipeline."""

import json
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from rag.generator.review_generator import ReviewConfig, ReviewGenerator
from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher
from rag.retriever.vector_store import VectorStore

PROFILE_ID = "octocat"

# Each prompt template opens with distinct wording, which lets the fake LLM tell which
# section it is being asked for without the generator passing that name to the API.
SECTION_MARKERS = (
    ("skills demonstrated", "skills_feedback"),
    ("quality and presentation of projects", "projects_feedback"),
    ("overall presentation quality", "presentation_feedback"),
    ("skill gaps relative to job market", "gaps_feedback"),
    ("first impression", "first_impression"),
)

JSON_SECTIONS = (
    "skills_feedback",
    "projects_feedback",
    "presentation_feedback",
    "gaps_feedback",
)

PROSE_RESPONSE = "A focused backend portfolio with room to grow."

CHUNK_TEXTS = [
    "Python FastAPI backend service with pytest coverage and Docker deployment",
    "Python Flask backend API with pytest fixtures and Docker packaging",
    "React TypeScript frontend dashboard built with Tailwind and Vite",
    "Machine learning pipeline in Python using scikit-learn and pandas",
    "Go microservice exposing gRPC endpoints with Kubernetes manifests",
    "Terraform modules provisioning managed Postgres and Redis instances",
]

FENCE = "```json"


@dataclass
class StoredChunk:
    """Minimal chunk record satisfying VectorStore.add_chunks().

    add_chunks() reads id, text, source_id, chunk_index and section off each chunk,
    which the chunking layer's Chunk dataclass does not currently provide.
    """

    id: str
    text: str
    source_id: str
    chunk_index: int
    section: str = "readme"


class FakeMessage:
    """Stand-in for a chat completion message."""

    def __init__(self, content):
        self.content = content


class FakeChoice:
    """Stand-in for a chat completion choice."""

    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    """Stand-in for a chat completion response."""

    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    """Stand-in for client.chat.completions."""

    def __init__(self, owner):
        self._owner = owner

    def create(self, **kwargs):
        """Delegate to the owning client so the call is recorded."""
        return self._owner.respond(kwargs)


class FakeChat:
    """Stand-in for client.chat."""

    def __init__(self, owner):
        self.completions = FakeCompletions(owner)


class FakeOpenAIClient:
    """Deterministic openai.OpenAI replacement answering per requested section.

    Hand-rolled rather than a MagicMock because a MagicMock's
    response.choices[0].message.content is itself a Mock, which the output parser
    would silently route through its plaintext fallback instead of failing.
    """

    def __init__(self, fail_sections=None):
        self.fail_sections = set(fail_sections or ())
        self.calls = []
        self.chat = FakeChat(self)

    @staticmethod
    def classify(prompt):
        """Return the section name the prompt is asking about."""
        for marker, section_name in SECTION_MARKERS:
            if marker in prompt:
                return section_name
        return "unknown_section"

    def respond(self, kwargs):
        """Build a fake response for one chat.completions.create() call."""
        prompt = kwargs["messages"][1]["content"]
        section_name = self.classify(prompt)
        self.calls.append({"section": section_name, "kwargs": kwargs})

        if section_name in self.fail_sections:
            raise RuntimeError("simulated LLM failure")

        # The first_impression template explicitly asks for prose, not JSON, so this
        # exercises the parser's plaintext fallback alongside the four JSON sections.
        if section_name == "first_impression":
            return FakeResponse(PROSE_RESPONSE)

        # Each section must answer under its own top-level key: generate_section() takes
        # the section name from the parsed payload, and _consolidate_feedback() then
        # de-duplicates by that name, so a shared key would collapse five into one.
        payload = {
            section_name: {
                "summary": "Assessment for " + section_name,
                "suggestions": ["Improve " + section_name],
            }
        }
        return FakeResponse(FENCE + "\n" + json.dumps(payload) + "\n```")


@pytest.mark.integration
class TestRagPipeline:
    """Test suite for the end-to-end RAG pipeline."""

    @pytest.fixture(autouse=True)
    def offline(self, monkeypatch):
        """Keep Chroma from phoning home so the pipeline runs fully offline."""
        monkeypatch.setenv("ANONYMIZED_TELEMETRY", "False")

    @pytest.fixture
    def embedder(self):
        """Return the deterministic mock embedding provider."""
        return MockEmbeddingProvider()

    @pytest.fixture
    def chunk_records(self):
        """Return chunk records for the seeded profile, one source each."""
        return [
            StoredChunk(id=f"chunk_{i}", text=text, source_id=f"repo_{i}", chunk_index=i)
            for i, text in enumerate(CHUNK_TEXTS)
        ]

    @pytest.fixture
    def retriever(self, tmp_path, embedder, chunk_records):
        """Build a HybridRetriever over a seeded on-disk Chroma collection."""
        store = VectorStore(persist_dir=str(tmp_path / "chroma"))
        embeddings = embedder.embed([record.text for record in chunk_records])
        store.add_chunks(list(zip(chunk_records, embeddings, strict=True)), f"profile_{PROFILE_ID}")

        # HybridRetriever.retrieve() never indexes the searcher itself, so the caller
        # has to, or the keyword arm contributes nothing.
        searcher = KeywordSearcher()
        searcher.index(
            [
                {
                    "id": record.id,
                    "text": record.text,
                    "metadata": {
                        "source_id": record.source_id,
                        "chunk_index": record.chunk_index,
                        "section": record.section,
                    },
                }
                for record in chunk_records
            ]
        )
        return HybridRetriever(store, searcher)

    @pytest.fixture
    def empty_retriever(self, tmp_path):
        """Build a HybridRetriever with no vectors and no keyword index."""
        store = VectorStore(persist_dir=str(tmp_path / "chroma_ghost"))
        return HybridRetriever(store, KeywordSearcher())

    @pytest.fixture
    def profile_data(self):
        """Return profile metadata passed to the generator."""
        return {"github_username": PROFILE_ID, "projects": [{"name": "a"}, {"name": "b"}]}

    @staticmethod
    def synthetic_chunks(count):
        """Return retriever-shaped chunk dicts with one distinct source each."""
        return [
            {
                "id": f"synthetic_{i}",
                "text": f"Synthetic portfolio evidence number {i}",
                "metadata": {"source_id": f"source_{i}", "chunk_index": i, "section": "readme"},
                "score": 0.9 - i / 100,
            }
            for i in range(count)
        ]

    @staticmethod
    def run_generation(fake_client, profile_data, chunks):
        """Run generate_full_review() against the fake OpenAI client."""
        config = ReviewConfig(
            api_key="test-key",
            base_url="http://llm.invalid/v1",
            model="test-model",
            temperature=0.2,
            max_tokens=256,
        )
        # Only construction needs patching; the client is then held on the instance.
        with patch("rag.generator.review_generator.openai.OpenAI", return_value=fake_client):
            generator = ReviewGenerator(config)
        return generator.generate_full_review(profile_data, chunks)

    def test_retrieval_blends_vector_and_keyword_scores(self, retriever, embedder):
        """Test that retrieved chunks carry blended scores from both retrieval arms."""
        query = CHUNK_TEXTS[0]
        results = retriever.retrieve(
            query, PROFILE_ID, embedder.embed([query])[0], max_chunks=len(CHUNK_TEXTS)
        )

        # Deliberately a range, not an exact count: how many chunks clear min_score
        # depends on the vector score conversion, which is not what this test pins.
        assert 1 <= len(results) <= len(CHUNK_TEXTS)
        for chunk in results:
            assert set(chunk) == {
                "id",
                "text",
                "metadata",
                "score",
                "vector_score",
                "keyword_score",
            }
            assert chunk["score"] == pytest.approx(
                0.7 * chunk["vector_score"] + 0.3 * chunk["keyword_score"]
            )
            assert chunk["vector_score"] > 0
            # BM25 legitimately scores zero for a chunk sharing no query terms.
            assert chunk["keyword_score"] >= 0

        top = results[0]
        assert top["id"] == "chunk_0"
        assert top["text"] == CHUNK_TEXTS[0]
        # Metadata survived the round-trip through Chroma with its values intact.
        assert top["metadata"] == {"source_id": "repo_0", "chunk_index": 0, "section": "readme"}
        # The query is chunk 0's own text, so the keyword arm must have contributed.
        assert top["keyword_score"] > 0
        scores = [chunk["score"] for chunk in results]
        assert scores == sorted(scores, reverse=True)

    def test_min_score_threshold_filters_weak_matches(self, retriever, embedder):
        """Test that min_score is applied to blended scores rather than ignored."""
        query = CHUNK_TEXTS[0]
        embedding = embedder.embed([query])[0]
        lenient = retriever.retrieve(query, PROFILE_ID, embedding, max_chunks=len(CHUNK_TEXTS))
        assert lenient

        # Both arms are max-normalised, so no blended score can exceed 0.7 + 0.3; a
        # threshold above that must filter everything however scores are computed.
        assert retriever.retrieve(query, PROFILE_ID, embedding, min_score=1.01) == []

        strict = retriever.retrieve(
            query, PROFILE_ID, embedding, max_chunks=len(CHUNK_TEXTS), min_score=0.9
        )
        assert len(strict) <= len(lenient)
        for chunk in strict:
            assert chunk["score"] >= 0.9

    def test_pipeline_produces_all_sections_with_citations(self, retriever, embedder, profile_data):
        """Test that retrieval feeds generation and yields five distinct cited sections."""
        query = "python backend pytest docker"
        chunks = retriever.retrieve(query, PROFILE_ID, embedder.embed([query])[0], max_chunks=3)
        assert chunks

        client = FakeOpenAIClient()
        sections = self.run_generation(client, profile_data, chunks)

        assert [call["section"] for call in client.calls] == [
            "skills_feedback",
            "projects_feedback",
            "presentation_feedback",
            "gaps_feedback",
            "first_impression",
        ]
        assert len(sections) == 5
        by_name = {section.section_name: section for section in sections}
        assert set(JSON_SECTIONS) <= set(by_name)

        # The prose section is matched on content, not name: generate_section() takes the
        # name from the parsed payload, so the plaintext reply keeps the parser's own
        # label. Asserting content holds whether or not that is later corrected.
        prose = [section for section in sections if section.content.startswith(PROSE_RESPONSE)]
        assert len(prose) == 1
        assert prose[0].confidence == pytest.approx(0.7)

        expected = sorted({chunk["metadata"]["source_id"] for chunk in chunks[:5]})
        assert len(expected) == len(chunks)
        for section in sections:
            assert section.content.endswith("Sources: " + ", ".join(expected))

    def test_json_response_parses_into_structured_section(self, retriever, embedder, profile_data):
        """Test that fenced JSON responses become high-confidence parsed sections."""
        query = CHUNK_TEXTS[3]
        chunks = retriever.retrieve(query, PROFILE_ID, embedder.embed([query])[0])
        sections = self.run_generation(FakeOpenAIClient(), profile_data, chunks)
        # Keyed by the payload's section name, which the fake echoes back deliberately.
        by_name = {section.section_name: section for section in sections}

        skills = by_name["skills_feedback"]
        assert skills.confidence == pytest.approx(0.9)
        assert skills.suggestions == ["Improve skills_feedback"]
        payload = json.loads(skills.content.split("\nSources:")[0])
        assert payload["summary"] == "Assessment for skills_feedback"

    def test_prompt_carries_retrieved_context_and_profile_data(
        self, retriever, embedder, profile_data
    ):
        """Test that retrieved chunk text and profile metadata reach the LLM prompt."""
        query = CHUNK_TEXTS[0]
        chunks = retriever.retrieve(query, PROFILE_ID, embedder.embed([query])[0], max_chunks=2)
        client = FakeOpenAIClient()
        self.run_generation(client, profile_data, chunks)

        first = client.calls[0]["kwargs"]
        prompt = first["messages"][1]["content"]
        for position, chunk in enumerate(chunks, start=1):
            assert chunk["text"] in prompt
            assert "Source: " + chunk["metadata"]["source_id"] in prompt
            assert f"[{position}] (relevance:" in prompt
        assert "GitHub Username: " + PROFILE_ID in prompt
        assert "Project Count: 2" in prompt
        assert first["model"] == "test-model"
        assert first["temperature"] == pytest.approx(0.2)
        assert first["max_tokens"] == 256

    def test_every_context_chunk_reaches_prompt_and_citations_cap_at_five(self, profile_data):
        """Test that all chunks reach the prompt while citations stop at five sources."""
        chunks = self.synthetic_chunks(6)
        client = FakeOpenAIClient()
        sections = self.run_generation(client, profile_data, chunks)

        prompt = client.calls[0]["kwargs"]["messages"][1]["content"]
        for position, chunk in enumerate(chunks, start=1):
            assert chunk["text"] in prompt
            assert f"[{position}] (relevance:" in prompt

        expected = sorted(chunk["metadata"]["source_id"] for chunk in chunks[:5])
        assert len(expected) == 5
        for section in sections:
            assert section.content.endswith("Sources: " + ", ".join(expected))
            assert chunks[5]["metadata"]["source_id"] not in section.content

    def test_empty_retrieval_still_generates_uncited_sections(
        self, empty_retriever, embedder, profile_data
    ):
        """Test that a profile with no indexed chunks degrades to uncited feedback."""
        query = "python backend testing"
        chunks = empty_retriever.retrieve(query, "ghost-profile", embedder.embed([query])[0])
        assert chunks == []

        client = FakeOpenAIClient()
        sections = self.run_generation(client, profile_data, chunks)

        assert len(client.calls) == 5
        assert len(sections) == 5
        for section in sections:
            assert "Sources:" not in section.content

    def test_single_section_llm_failure_yields_placeholder(self, retriever, embedder, profile_data):
        """Test that one failing LLM call degrades only that section."""
        query = CHUNK_TEXTS[2]
        chunks = retriever.retrieve(query, PROFILE_ID, embedder.embed([query])[0])
        client = FakeOpenAIClient(fail_sections={"gaps_feedback"})
        sections = self.run_generation(client, profile_data, chunks)

        by_name = {section.section_name: section for section in sections}
        placeholder = by_name["gaps_feedback"]
        assert placeholder.content == "Error generating gaps_feedback"
        assert placeholder.confidence == pytest.approx(0.0)
        assert placeholder.suggestions == []
        # The failure path skips citation appending, unlike the successful sections.
        assert "Sources:" not in placeholder.content
        assert len(client.calls) == 5
        assert len(sections) == 5
        assert by_name["skills_feedback"].confidence == pytest.approx(0.9)
