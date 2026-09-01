import logging
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


class FakeClientPorProjeto:
    """Cliente falso que respeita o filtro de escopo lógico do scroll."""

    def __init__(self, pontos_por_projeto: dict[str, list[str]]) -> None:
        self.pontos_por_projeto = pontos_por_projeto
        self.upserts = []
        self.deletes = []
        self.gravados: set[str] = set()
        self.confirmar_gravacao = True

    def get_collections(self):
        return SimpleNamespace(collections=[SimpleNamespace(name="collection")])

    def count(self, _collection_name):
        return SimpleNamespace(
            count=sum(len(v) for v in self.pontos_por_projeto.values())
        )

    def scroll(self, **kwargs):
        alvo = kwargs["scroll_filter"].must[0].match.value
        existentes = list(self.pontos_por_projeto.get(alvo, []))
        if self.confirmar_gravacao:
            existentes += [i for i in sorted(self.gravados) if i not in existentes]
        return [SimpleNamespace(id=ponto) for ponto in existentes], None

    def upsert(self, **kwargs):
        self.upserts.append(kwargs)
        if self.confirmar_gravacao:
            self.gravados.update(str(ponto.id) for ponto in kwargs["points"])

    def delete(self, **kwargs):
        self.deletes.append(kwargs)


def test_reexecucao_identica_nao_altera_a_base_e_registra_contagens(
    monkeypatch, tmp_path, caplog
) -> None:
    # SPECSFY: US-001 FR-003 NFR-002 NFR-003 AC-004
    chunk_id = str(uuid4())
    client = FakeClientPorProjeto({"projeto": [chunk_id]})
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    with caplog.at_level(logging.INFO):
        embedder.index_chunks(
            [_chunk(chunk_id)], embedding_cfg, vector_cfg, str(tmp_path)
        )

    assert client.upserts == []
    assert client.deletes == []
    registro = " ".join(item.getMessage().lower() for item in caplog.records)
    for termo in ("previstos", "inseridos", "mantidos", "removidos"):
        assert termo in registro


def test_falha_de_upsert_em_lote_posterior_nao_inicia_a_limpeza(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-001 FR-003 FR-004 NFR-001 AC-005
    obsoleto = str(uuid4())
    client = FakeClient([obsoleto])
    client.fail_upsert = True
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    with pytest.raises(RuntimeError):
        embedder.index_chunks(
            [_chunk(str(uuid4())), _chunk(str(uuid4()))],
            embedding_cfg,
            vector_cfg,
            str(tmp_path),
        )

    assert client.deletes == []


def test_espelho_nunca_le_nem_remove_pontos_de_outro_projeto(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-001 FR-003 FR-004 NFR-003 AC-006
    obsoleto = str(uuid4())
    preservado = str(uuid4())
    intocado = str(uuid4())
    client = FakeClientPorProjeto(
        {"projeto": [obsoleto, preservado], "outro": [intocado]}
    )
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    embedder.index_chunks(
        [_chunk(preservado), _chunk(str(uuid4()))],
        embedding_cfg,
        vector_cfg,
        str(tmp_path),
    )

    removidos = [
        ponto
        for chamada in client.deletes
        for ponto in chamada["points_selector"].points
    ]
    assert removidos == [obsoleto]
    assert intocado not in removidos


def test_registro_da_sincronizacao_nao_expoe_segredos(
    monkeypatch, tmp_path, caplog
) -> None:
    # SPECSFY: US-001 FR-003 FR-006 NFR-002 AC-010
    client = FakeClientPorProjeto({"projeto": [str(uuid4())]})
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())
    monkeypatch.setenv("QDRANT_URL", "https://destino-secreto.example")
    monkeypatch.setenv("QDRANT_API_KEY", "chave-secreta")

    with caplog.at_level(logging.INFO):
        embedder.index_chunks(
            [_chunk(str(uuid4()))], embedding_cfg, vector_cfg, str(tmp_path)
        )

    registro = " ".join(item.getMessage() for item in caplog.records)
    assert "projeto" in registro
    for termo in ("previstos", "inseridos", "mantidos", "removidos"):
        assert termo in registro.lower()
    assert "destino-secreto.example" not in registro
    assert "chave-secreta" not in registro


def test_limpeza_bloqueada_quando_o_destino_nao_confirma_os_esperados(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-001 AC-014
    obsoleto = str(uuid4())
    client = FakeClientPorProjeto({"projeto": [obsoleto]})
    client.confirmar_gravacao = False
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    with pytest.raises(ValueError, match="confirm"):
        embedder.index_chunks(
            [_chunk(str(uuid4()))], embedding_cfg, vector_cfg, str(tmp_path)
        )

    assert client.deletes == []


def test_substituicao_total_do_escopo_permanece_permitida(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-003 AC-015
    anterior_a = str(uuid4())
    anterior_b = str(uuid4())
    client = FakeClientPorProjeto({"projeto": [anterior_a, anterior_b]})
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setattr(embedder, "_get_qdrant_client", lambda: client)
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: FakeEmbeddings())

    novo_a, novo_b = str(uuid4()), str(uuid4())
    embedder.index_chunks(
        [_chunk(novo_a), _chunk(novo_b)], embedding_cfg, vector_cfg, str(tmp_path)
    )

    removidos = {
        ponto
        for chamada in client.deletes
        for ponto in chamada["points_selector"].points
    }
    assert removidos == {anterior_a, anterior_b}
    assert client.gravados == {novo_a, novo_b}
