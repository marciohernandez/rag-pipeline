"""Caracterização das operações do backend real do Qdrant — SPEC-0011.

A suíte de conformidade injeta `FakeVectorBackend`/`DictVectorBackend`, então
`_create_backend()` nunca roda e o código que fala com o SDK do Qdrant não tem
prova além de `describe` (SPEC-0004, `tests/test_describe_scope_backends.py`).
Aqui o `_QdrantBackend` real é construído de verdade e só `_conn()` é
substituído por um dublê mínimo por operação, sem rede.
"""

from __future__ import annotations

import pytest

from src.pipeline.providers.contracts import LogicalScope, VectorRecord
from src.pipeline.providers.errors import UnreliableScopeReadError

ESCOPO = LogicalScope(project_id="projeto", tenant_id="cliente")
ESCOPO_SEM_TENANT = LogicalScope(project_id="projeto")


def _qdrant(monkeypatch, cliente):
    from src.pipeline.providers.vectorstores.qdrant import _QdrantBackend

    backend = _QdrantBackend("colecao", "http://destino", "chave")
    monkeypatch.setattr(backend, "_conn", lambda: cliente)
    return backend


# ---------------------------------------------------------------------------
# ensure
# ---------------------------------------------------------------------------


class _ColecaoNomeada:
    def __init__(self, name: str) -> None:
        self.name = name


class _RespostaColecoes:
    def __init__(self, nomes: list[str]) -> None:
        self.collections = [_ColecaoNomeada(nome) for nome in nomes]


class _ClienteEnsure:
    def __init__(self, *, colecoes_existentes: tuple[str, ...] = (), falha: bool = False) -> None:
        self.colecoes_existentes = list(colecoes_existentes)
        self.falha = falha
        self.chamadas: list[str] = []
        self.create_kwargs: dict | None = None

    def get_collections(self):
        self.chamadas.append("get_collections")
        if self.falha:
            raise RuntimeError("SDK indisponível")
        return _RespostaColecoes(self.colecoes_existentes)

    def create_collection(self, **kwargs):
        self.chamadas.append("create_collection")
        self.create_kwargs = kwargs


def test_ensure_cria_colecao_quando_ausente(monkeypatch) -> None:
    # SPECSFY: FR-001 NFR-001 AC-001
    cliente = _ClienteEnsure(colecoes_existentes=())
    backend = _qdrant(monkeypatch, cliente)

    backend.ensure(ESCOPO, dimensions=8)

    assert cliente.chamadas == ["get_collections", "create_collection"]
    assert cliente.create_kwargs["collection_name"] == "colecao"
    vectors_config = cliente.create_kwargs["vectors_config"]
    assert vectors_config.size == 8
    from qdrant_client.http.models import Distance

    assert vectors_config.distance == Distance.COSINE


def test_ensure_nao_recria_colecao_existente(monkeypatch) -> None:
    # SPECSFY: FR-001 NFR-001 AC-002
    cliente = _ClienteEnsure(colecoes_existentes=("colecao",))
    backend = _qdrant(monkeypatch, cliente)

    backend.ensure(ESCOPO, dimensions=8)

    assert cliente.chamadas == ["get_collections"]


def test_ensure_propaga_falha_do_sdk(monkeypatch) -> None:
    # SPECSFY: FR-001 NFR-001 AC-003
    cliente = _ClienteEnsure(falha=True)
    backend = _qdrant(monkeypatch, cliente)

    with pytest.raises(RuntimeError, match="SDK indisponível"):
        backend.ensure(ESCOPO, dimensions=8)


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------


class _ClienteWrite:
    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.upsert_kwargs: dict | None = None

    def upsert(self, **kwargs):
        self.chamadas.append("upsert")
        self.upsert_kwargs = kwargs


def test_write_traduz_pointstruct(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001 AC-004
    cliente = _ClienteWrite()
    backend = _qdrant(monkeypatch, cliente)
    registro = VectorRecord(
        id="chunk-1",
        content="conteudo do chunk",
        vector=[0.1, 0.2, 0.3],
        metadata={"project_id": "projeto", "tenant_id": "cliente"},
    )

    backend.write(ESCOPO, [registro])

    assert cliente.chamadas == ["upsert"]
    assert cliente.upsert_kwargs["collection_name"] == "colecao"
    assert cliente.upsert_kwargs["wait"] is True
    (ponto,) = cliente.upsert_kwargs["points"]
    assert ponto.id == "chunk-1"
    assert list(ponto.vector) == [0.1, 0.2, 0.3]
    assert ponto.payload["page_content"] == "conteudo do chunk"
    assert ponto.payload["metadata"] == {"project_id": "projeto", "tenant_id": "cliente"}


def test_write_lista_vazia_e_no_op(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001 AC-005
    cliente = _ClienteWrite()
    backend = _qdrant(monkeypatch, cliente)

    backend.write(ESCOPO, [])

    assert cliente.chamadas == []


def test_write_preserva_ordem_e_contagem(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001 AC-006
    cliente = _ClienteWrite()
    backend = _qdrant(monkeypatch, cliente)
    registros = [
        VectorRecord(
            id=f"chunk-{indice}", content=f"c{indice}", vector=[float(indice)], metadata={}
        )
        for indice in range(5)
    ]

    backend.write(ESCOPO, registros)

    pontos = cliente.upsert_kwargs["points"]
    assert len(pontos) == 5
    assert [ponto.id for ponto in pontos] == [f"chunk-{indice}" for indice in range(5)]


class _ClienteWriteLotes:
    """Acumula cada chamada a ``upsert`` para inspecionar o lote enviado."""

    def __init__(self) -> None:
        self.lotes: list[list] = []

    def upsert(self, **kwargs):
        self.lotes.append(list(kwargs["points"]))


def test_write_loteia_upsert_acima_do_limite(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001 AC-006
    # Regressão (achado no E2E de 2026-09-07): um único ``upsert`` com centenas
    # de vetores de 1536 dimensões estourava o timeout de escrita do SDK em
    # endpoint atrás de proxy. ``write`` passa a lotear em blocos de
    # ``_UPSERT_BATCH`` pontos, preservando ordem e contagem globais.
    from src.pipeline.providers.vectorstores import qdrant

    cliente = _ClienteWriteLotes()
    backend = _qdrant(monkeypatch, cliente)
    total = qdrant._UPSERT_BATCH * 2 + 3
    registros = [
        VectorRecord(id=f"chunk-{i}", content=f"c{i}", vector=[float(i)], metadata={})
        for i in range(total)
    ]

    backend.write(ESCOPO, registros)

    assert [len(lote) for lote in cliente.lotes] == [
        qdrant._UPSERT_BATCH,
        qdrant._UPSERT_BATCH,
        3,
    ]
    ids = [ponto.id for lote in cliente.lotes for ponto in lote]
    assert ids == [f"chunk-{i}" for i in range(total)]


def test_build_client_define_timeout_explicito(monkeypatch) -> None:
    # SPECSFY: FR-002 NFR-001
    # Regressão (achado no E2E de 2026-09-07): ``QdrantClient`` era criado sem
    # ``timeout``, herdando o padrão de ~5 s do SDK REST — curto demais para
    # escrita/leitura em endpoint publicado por proxy.
    import qdrant_client

    from src.pipeline.providers.vectorstores import qdrant

    capturado: dict = {}

    class _FakeQdrantClient:
        def __init__(self, **kwargs):
            capturado.update(kwargs)

    monkeypatch.setattr(qdrant_client, "QdrantClient", _FakeQdrantClient)

    qdrant._build_client("https://qdrant.example.com", "chave")

    assert capturado["timeout"] == qdrant._CLIENT_TIMEOUT
    assert capturado["timeout"] >= 30


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class _Hit:
    def __init__(self, payload: dict, score: float) -> None:
        self.payload = payload
        self.score = score


class _ClienteSearch:
    def __init__(self, hits: tuple = ()) -> None:
        self.hits = list(hits)
        self.chamadas: list[str] = []
        self.search_kwargs: dict | None = None

    def search(self, **kwargs):
        self.chamadas.append("search")
        self.search_kwargs = kwargs
        return self.hits


def test_search_traduz_filtro_com_tenant_e_resposta(monkeypatch) -> None:
    # SPECSFY: FR-003 NFR-001 AC-007
    hit = _Hit(payload={"page_content": "texto", "metadata": {"a": 1}}, score=0.87)
    cliente = _ClienteSearch(hits=(hit,))
    backend = _qdrant(monkeypatch, cliente)

    resultados = backend.search(ESCOPO, embedding=[0.1, 0.2], k=3)

    assert cliente.chamadas == ["search"]
    filtro = cliente.search_kwargs["query_filter"]
    condicoes = {condicao.key: condicao.match.value for condicao in filtro.must}
    assert condicoes == {"metadata.project_id": "projeto", "metadata.tenant_id": "cliente"}
    assert len(resultados) == 1
    assert resultados[0].content == "texto"
    assert resultados[0].metadata == {"a": 1}
    assert resultados[0].score == pytest.approx(0.87)


def test_search_sem_tenant_filtra_so_project_id(monkeypatch) -> None:
    # SPECSFY: FR-003 NFR-001 AC-008
    cliente = _ClienteSearch(hits=())
    backend = _qdrant(monkeypatch, cliente)

    backend.search(ESCOPO_SEM_TENANT, embedding=[0.1], k=1)

    filtro = cliente.search_kwargs["query_filter"]
    chaves = {condicao.key for condicao in filtro.must}
    assert chaves == {"metadata.project_id"}


def test_search_sem_hits_devolve_lista_vazia(monkeypatch) -> None:
    # SPECSFY: FR-003 NFR-001 AC-009
    cliente = _ClienteSearch(hits=())
    backend = _qdrant(monkeypatch, cliente)

    resultados = backend.search(ESCOPO, embedding=[0.1], k=5)

    assert resultados == []


# ---------------------------------------------------------------------------
# scope_ids
# ---------------------------------------------------------------------------


class _Registro:
    def __init__(self, id: str) -> None:
        self.id = id


class _ClienteScopeIds:
    def __init__(self, *, paginas: list | None = None, falha: bool = False) -> None:
        self.paginas = list(paginas or [])
        self.falha = falha
        self.chamadas = 0

    def scroll(self, **_kwargs):
        self.chamadas += 1
        if self.falha:
            raise RuntimeError("scroll indisponível")
        return self.paginas.pop(0)


def test_scope_ids_agrega_paginas(monkeypatch) -> None:
    # SPECSFY: FR-004 NFR-001 AC-010
    pagina1 = ([_Registro("a"), _Registro("b")], "cursor-1")
    pagina2 = ([_Registro("c")], None)
    cliente = _ClienteScopeIds(paginas=[pagina1, pagina2])
    backend = _qdrant(monkeypatch, cliente)

    resultado = backend.scope_ids(ESCOPO)

    assert resultado == {"a", "b", "c"}
    assert cliente.chamadas == 2


def test_scope_ids_pagina_unica(monkeypatch) -> None:
    # SPECSFY: FR-004 NFR-001 AC-011
    pagina_unica = ([_Registro("a")], None)
    cliente = _ClienteScopeIds(paginas=[pagina_unica])
    backend = _qdrant(monkeypatch, cliente)

    resultado = backend.scope_ids(ESCOPO)

    assert resultado == {"a"}
    assert cliente.chamadas == 1


def test_scope_ids_traduz_falha_do_sdk(monkeypatch) -> None:
    # SPECSFY: FR-004 NFR-001 AC-012
    cliente = _ClienteScopeIds(falha=True)
    backend = _qdrant(monkeypatch, cliente)

    with pytest.raises(UnreliableScopeReadError):
        backend.scope_ids(ESCOPO)


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


class _ClienteRemove:
    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.delete_kwargs: dict | None = None

    def delete(self, **kwargs):
        self.chamadas.append("delete")
        self.delete_kwargs = kwargs


def test_remove_traduz_pointidslist(monkeypatch) -> None:
    # SPECSFY: FR-005 NFR-001 AC-013
    cliente = _ClienteRemove()
    backend = _qdrant(monkeypatch, cliente)

    backend.remove(ESCOPO, ["a", "b"])

    assert cliente.chamadas == ["delete"]
    assert cliente.delete_kwargs["collection_name"] == "colecao"
    assert cliente.delete_kwargs["wait"] is True
    assert set(cliente.delete_kwargs["points_selector"].points) == {"a", "b"}


def test_remove_lista_vazia_e_no_op(monkeypatch) -> None:
    # SPECSFY: FR-005 NFR-001 AC-014
    cliente = _ClienteRemove()
    backend = _qdrant(monkeypatch, cliente)

    backend.remove(ESCOPO, [])

    assert cliente.chamadas == []


def test_remove_aceita_generator(monkeypatch) -> None:
    # SPECSFY: FR-005 NFR-001 AC-015
    cliente = _ClienteRemove()
    backend = _qdrant(monkeypatch, cliente)

    def gerador():
        yield "x"
        yield "y"

    backend.remove(ESCOPO, gerador())

    assert set(cliente.delete_kwargs["points_selector"].points) == {"x", "y"}
