import os
import sys
import types
import time
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def set_env_vars() -> None:
    os.environ.setdefault("GEMINI_API_KEY", "test-key")


class FakeEmbeddings:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 3 for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [0.0, 0.0, 0.0]


class FakeCrossEncoder:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def predict(self, pairs: List[List[str]]) -> List[float]:
        return [1.0 for _ in pairs]


class FakeCompressor:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def compress_documents(self, docs: List[Any], query: str) -> List[Any]:
        return docs[:5]


class FakeDoc:
    def __init__(self, page_content: str, metadata: Dict[str, Any] | None = None) -> None:
        self.page_content = page_content
        self.metadata = metadata or {}


class FakeChroma:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []

    # Methods used in process_upload
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        self._texts.extend(texts)
        self._metas.extend(metadatas)

    def persist(self) -> None:
        return

    # Methods used in answer_query (not essential for upload test)
    def similarity_search(self, query: str, k: int = 4) -> List[FakeDoc]:
        return [FakeDoc(page_content=t, metadata=(self._metas[i] if i < len(self._metas) else {})) for i, t in enumerate(self._texts[:k])]


def test_upload_with_stubbed_vectorstore() -> None:
    # Preload stub modules so service imports use fakes and avoid heavy downloads
    sys.modules['langchain_huggingface'] = types.SimpleNamespace(
        HuggingFaceEmbeddings=FakeEmbeddings
    )
    sys.modules['langchain_community.cross_encoders'] = types.SimpleNamespace(
        HuggingFaceCrossEncoder=FakeCrossEncoder
    )
    sys.modules['langchain_community.vectorstores'] = types.SimpleNamespace(
        Chroma=FakeChroma
    )
    # Stub utils module referenced in knowledge_service (safe no-op)
    sys.modules['langchain_community.vectorstores.utils'] = types.SimpleNamespace(
        filter_complex_metadata=lambda x: x
    )
    # Stub google genai client to avoid external calls if answer_query is ever touched
    fake_generate = lambda **kwargs: types.SimpleNamespace(text="OK")
    sys.modules['google'] = types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=lambda api_key: types.SimpleNamespace(models=types.SimpleNamespace(generate_content=fake_generate)))
    )

    # Import after setting env and patching to avoid heavy downloads
    import app.services.knowledge.knowledge_service as ks

    # Patch heavy components
    ks.embeddings = FakeEmbeddings()
    ks.reranker_model = FakeCrossEncoder()
    ks.compressor = FakeCompressor()
    ks.Chroma = FakeChroma  # type: ignore

    # Build app client
    from app.main import app
    client = TestClient(app)

    # Use provided file
    file_path = os.path.join("data_set", "files", "saudi_labor_law.json")
    assert os.path.exists(file_path), "Test input file not found"

    with open(file_path, "rb") as f:
        files = {"file": ("saudi_labor_law.json", f, "application/json")}
        start = time.time()
        resp = client.post("/api/v1/rag/upload", files=files)
        elapsed = time.time() - start

    # Basic assertions on unified API response structure
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload, dict)
    assert payload.get("success") is True
    assert payload.get("data") is not None
    assert isinstance(payload.get("errors"), list)

    data = payload["data"]
    assert "filename" in data
    assert "chunks_created" in data
    assert data.get("status") == "processed"

    # Sanity check on performance for stubbed run
    # Should complete quickly (< 3s) when stubbed
    assert elapsed < 3.0, f"Upload processing took too long: {elapsed:.2f}s"


