"""Caracterização de `describe` nos backends reais — SPEC-0004.

A suíte de conformidade injeta `FakeVectorBackend` como cliente, então
`_create_backend()` nunca roda e o código que traduz cada SDK fica sem prova.
Aqui os backends reais são construídos de verdade e o SDK é substituído por um
dublê, sem rede.
"""

from __future__ import annotations

from src.pipeline.providers.contracts import LogicalScope

ESCOPO = LogicalScope(project_id="projeto", tenant_id=None)


class _ColecaoQdrant:
    class config:
        class params:
            class vectors:
                size = 8


class _ClienteQdrant:
    def __init__(self, *, falha: bool = False) -> None:
        self.falha = falha
        self.chamadas: list[str] = []

    def get_collection(self, collection_name: str):
        self.chamadas.append("get_collection")
        if self.falha:
            raise RuntimeError("coleção inexistente")
        return _ColecaoQdrant()

    def create_collection(self, **_kwargs):  # pragma: no cover - não pode ocorrer
        raise AssertionError("describe não pode criar coleção")


def _qdrant(monkeypatch, cliente):
    from src.pipeline.providers.vectorstores.qdrant import _QdrantBackend

    backend = _QdrantBackend("colecao", "http://destino", "chave")
    monkeypatch.setattr(backend, "_conn", lambda: cliente)
    return backend


def test_qdrant_extrai_a_dimensao_declarada_pela_colecao(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-002 AC-003 AC-016
    cliente = _ClienteQdrant()
    backend = _qdrant(monkeypatch, cliente)

    assert backend.describe(ESCOPO) == {"exists": True, "dimensions": 8}
    assert cliente.chamadas == ["get_collection"]


def test_qdrant_com_colecao_ausente_devolve_mapa_vazio(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001 AC-003 AC-016
    backend = _qdrant(monkeypatch, _ClienteQdrant(falha=True))

    assert backend.describe(ESCOPO) == {}


# SPEC-0010: os casos de `describe` de ChromaDB e Pinecone foram removidos
# junto com os adapters. O `_QdrantBackend` é o único backend real restante e
# segue coberto acima.
