from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.documents import Document

import src.embedder as embedder


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeClient:
    def __init__(self, existing_ids: list[str], *, fail_upsert: bool = False) -> None:
        self.existing_ids = existing_ids
        self.fail_upsert = fail_upsert
        self.upserts = []
        self.deletes = []

    def get_collections(self):
        return SimpleNamespace(collections=[SimpleNamespace(name="collection")])

    def count(self, _collection_name):
        return SimpleNamespace(count=len(self.existing_ids))

    def scroll(self, **_kwargs):
        return [SimpleNamespace(id=point_id) for point_id in self.existing_ids], None

    def upsert(self, **kwargs):
        if self.fail_upsert:
            raise RuntimeError("falha de rede simulada")
        self.upserts.append(kwargs)

    def delete(self, **kwargs):
        self.deletes.append(kwargs)


def _chunk(chunk_id: str) -> Document:
    return Document(
        page_content="conteúdo",
        metadata={
            "project_id": "projeto",
            "document_id": str(uuid4()),
            "chunk_id": chunk_id,
            "chunk_type": "detail",
        },
    )


def _config() -> tuple[dict, dict]:
    return (
        {"provider": "openai", "model": "text-embedding-3-small", "dimensions": 3},
        {"provider": "qdrant", "collection_name": "collection", "sync_mode": "mirror"},
    )


def test_upserts_new_points_then_removes_only_stale_points(monkeypatch, tmp_path) -> None:
    stale_id = str(uuid4())
    current_id = str(uuid4())
    client = FakeClient([stale_id])
    embeddings = FakeEmbeddings()
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: embeddings)

    embedder.index_chunks(
        [_chunk(current_id)], embedding_cfg, vector_cfg, str(tmp_path)
    )

    assert len(client.upserts) == 1
    assert embeddings.calls == [["conteúdo"]]
    assert len(client.deletes) == 1
    assert client.deletes[0]["points_selector"].points == [stale_id]


def test_upsert_failure_never_removes_existing_points(monkeypatch, tmp_path) -> None:
    stale_id = str(uuid4())
    client = FakeClient([stale_id], fail_upsert=True)
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    with pytest.raises(RuntimeError, match="falha de rede"):
        embedder.index_chunks(
            [_chunk(str(uuid4()))], embedding_cfg, vector_cfg, str(tmp_path)
        )

    assert client.deletes == []
