"""Testes TDD da SPEC-0004 — validação de recuperação e operação.

Cada caso é derivado de um cenário BDD da seção 6 da spec e carrega seu
próprio marcador ``SPECSFY:``. O destino remoto é substituído por um adapter
observável que registra toda chamada, o que permite provar as garantias de
somente leitura sem tocar em rede.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from src.providers.contracts import LogicalScope, SearchResult


def _validacao():
    """Import tardio do módulo em construção.

    Mantém o RED isolado em cada caso: sem isto, o módulo ausente quebraria a
    coleta e apagaria o sinal de regressão do restante da suíte.
    """
    import src.validation as validation

    return validation

API_KEY = "chave-secreta-de-teste"
DESTINO = "https://destino-interno.exemplo/qdrant"


class RecordingAdapter:
    """Adapter observável: registra cada chamada recebida do validador."""

    def __init__(
        self,
        ids: set[str] | None = None,
        *,
        dimensions: int = 16,
        results: list[SearchResult] | None = None,
        scope_exists: bool = True,
    ) -> None:
        self._ids = set(ids or set())
        self._dimensions = dimensions
        self._results = results or []
        self._scope_exists = scope_exists
        self.calls: list[str] = []
        self.ensure_ready_calls = 0
        self.upsert_calls: list[object] = []
        self.deleted_ids: list[str] = []
        self.query_calls: list[tuple[Sequence[float], int]] = []

    # leitura -----------------------------------------------------------
    def describe_scope(self, scope: LogicalScope) -> dict:
        self.calls.append("describe_scope")
        if not self._scope_exists:
            return {}
        return {"exists": True, "dimensions": self._dimensions}

    def list_ids(self, scope: LogicalScope) -> set[str]:
        self.calls.append("list_ids")
        return set(self._ids)

    def query(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        self.calls.append("query")
        self.query_calls.append((list(embedding), k))
        return list(self._results[:k])

    # escrita: nenhuma delas pode ser chamada pela validação -------------
    def ensure_ready(self, scope: LogicalScope, *, dimensions: int) -> None:
        self.calls.append("ensure_ready")
        self.ensure_ready_calls += 1

    def upsert(self, scope: LogicalScope, records: Sequence[object]) -> None:
        self.calls.append("upsert")
        self.upsert_calls.append(list(records))

    def delete_ids(self, scope: LogicalScope, ids) -> None:
        self.calls.append("delete_ids")
        self.deleted_ids.extend(ids)


class StubEmbeddings:
    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 16

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.1] * 16 for _ in texts]


def _resultado(conteudo: str, arquivo: str, score: float = 0.9) -> SearchResult:
    return SearchResult(
        content=conteudo,
        metadata={"nome_arquivo": arquivo, "chunk_id": arquivo},
        score=score,
    )


def _base(tmp_path: Path, *, ids=("a", "b"), consultas=None, limiar=0.5) -> dict:
    """Escreve manifesto e gabarito e devolve a configuração da base."""
    saida = tmp_path / "output"
    saida.mkdir(parents=True, exist_ok=True)
    manifesto = {
        "run_id": "run-0001",
        "project_id": "Projeto",
        "collection_name": "colecao",
        "chunk_count": len(list(ids)),
        "chunk_ids": list(ids),
        "documents": [],
        "chunk_type_counts": {},
        "embedding": {"provider": "fake", "model": "fake", "dimensions": 16},
    }
    (saida / "manifest.json").write_text(
        json.dumps(manifesto), encoding="utf-8"
    )
    gabarito = tmp_path / "consultas.yaml"
    if consultas is not None:
        gabarito.write_text(consultas, encoding="utf-8")
    return {
        "projeto": {"nome": "Projeto"},
        "caminhos": {
            "output_dir": str(saida),
            "chunks_file": str(saida / "chunks.json"),
            "consultas_referencia": str(gabarito),
        },
        "embedding": {"provider": "fake", "dimensions": 16},
        "vector_store": {
            "provider": "in_memory",
            "collection_name": "colecao",
            "url": DESTINO,
            "api_key": API_KEY,
        },
        "validacao": {"limiar_minimo": limiar, "top_k": 4},
    }


GABARITO_OK = """
- pergunta: "Quais planos existem?"
  categoria: ampla
  deve_conter: ["500 Mega"]
- pergunta: "Quem tem desconto?"
  categoria: especifica
  documento_esperado: "regulamento.md"
- pergunta: "Qual a cor do cavalo branco?"
  categoria: sem_resposta
"""


def test_ac_001_base_integra_e_aprovada(tmp_path):
    # SPECSFY: US-001 FR-001 FR-005 FR-006 NFR-002 AC-001
    config = _base(tmp_path, ids=("a", "b"), consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.2)],
    )
    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "aprovado"
    assert validacao.exit_code(report) == 0
    assert Path(report.report_path).exists()


def test_ac_002_config_sem_gabarito_falha_antes_do_destino(tmp_path):
    # SPECSFY: US-001 FR-001 FR-006 NFR-004 AC-002
    config = _base(tmp_path, consultas=GABARITO_OK)
    config["caminhos"].pop("consultas_referencia")
    adapter = RecordingAdapter({"a", "b"})

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "impedido"
    assert validacao.exit_code(report) == 2
    assert adapter.calls == []


def test_ac_003_dimensao_divergente_encerra_sem_consulta(tmp_path):
    # SPECSFY: US-001 FR-002 FR-006 NFR-003 NFR-004 AC-003
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter({"a", "b"}, dimensions=1536)

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "impedido"
    assert validacao.exit_code(report) == 2
    assert "query" not in adapter.calls
    assert adapter.ensure_ready_calls == 0
    assert DESTINO not in report.impediment
    assert API_KEY not in report.impediment


def test_ac_004_gabarito_sem_categoria_bloqueia_antes_do_remoto(tmp_path):
    # SPECSFY: US-001 FR-002 NFR-004 AC-004
    config = _base(
        tmp_path,
        consultas='- pergunta: "Sem categoria declarada"\n  deve_conter: ["x"]\n',
    )
    adapter = RecordingAdapter({"a", "b"})

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "impedido"
    assert adapter.calls == []


def test_ac_005_chunk_faltante_reprova(tmp_path):
    # SPECSFY: US-002 FR-003 FR-006 NFR-001 AC-005
    config = _base(tmp_path, ids=("a", "b"), consultas=GABARITO_OK)
    adapter = RecordingAdapter({"a"})

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "reprovado"
    assert validacao.exit_code(report) == 1
    assert report.comparison.faltantes == {"b"}
    assert adapter.upsert_calls == []


def test_ac_006_identificador_orfao_reprova(tmp_path):
    # SPECSFY: US-002 FR-003 AC-006
    config = _base(tmp_path, ids=("a",), consultas=GABARITO_OK)
    adapter = RecordingAdapter({"a", "resto-antigo"})

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.outcome == "reprovado"
    assert report.comparison.orfaos == {"resto-antigo"}


def test_ac_007_conjuntos_identicos_confirmam_contagem(tmp_path):
    # SPECSFY: US-002 FR-003 NFR-001 AC-007
    config = _base(tmp_path, ids=("a", "b", "c"), consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b", "c"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.2)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert report.comparison.faltantes == set()
    assert report.comparison.orfaos == set()
    assert report.comparison.previstos == report.comparison.observados == 3
    assert adapter.upsert_calls == [] and adapter.deleted_ids == []


def test_ac_008_documento_esperado_ausente_reprova(tmp_path):
    # SPECSFY: US-003 FR-004 AC-008
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "outro-arquivo.md", 0.2)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    especifica = next(item for item in report.queries if item.categoria == "especifica")
    assert especifica.aprovada is False
    assert "regulamento.md" in especifica.criterios_ausentes


def test_ac_009_item_de_deve_conter_ausente_reprova(tmp_path):
    # SPECSFY: US-003 FR-004 AC-009
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("apenas texto irrelevante", "regulamento.md", 0.2)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    ampla = next(item for item in report.queries if item.categoria == "ampla")
    assert ampla.aprovada is False
    assert "500 Mega" in ampla.criterios_ausentes


def test_ac_010_sem_resposta_acima_do_limiar_reprova(tmp_path):
    # SPECSFY: US-003 FR-004 FR-006 AC-010
    config = _base(tmp_path, consultas=GABARITO_OK, limiar=0.5)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.95)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    sem_resposta = next(
        item for item in report.queries if item.categoria == "sem_resposta"
    )
    assert sem_resposta.aprovada is False
    assert validacao.exit_code(report) == 1


def test_ac_011_relatorio_e_json_trazem_as_tres_etapas(tmp_path):
    # SPECSFY: US-001 US-002 US-003 FR-005 NFR-003 AC-011
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.2)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())
    gravado = json.loads(Path(report.report_path).read_text(encoding="utf-8"))
    legivel = report.render()

    for chave in ("preflight", "conferencia", "consultas", "desfecho"):
        assert chave in gravado
    assert gravado["conferencia"]["faltantes"] == []
    assert len(gravado["consultas"]) == 3
    assert "preflight" in legivel.lower()


def test_ac_012_saidas_nao_contem_segredo(tmp_path, caplog):
    # SPECSFY: US-001 FR-005 NFR-003 AC-012
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.2)],
    )

    validacao = _validacao()

    with caplog.at_level("INFO"):
        report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    bruto = Path(report.report_path).read_text(encoding="utf-8")
    for segredo in (API_KEY, DESTINO):
        assert segredo not in bruto
        assert segredo not in report.render()
        assert segredo not in caplog.text


def test_ac_013_falha_nao_produz_escrita(tmp_path):
    # SPECSFY: US-002 FR-002 NFR-001 AC-013
    config = _base(tmp_path, ids=("a", "b"), consultas=GABARITO_OK)
    adapter = RecordingAdapter({"a"})

    validacao = _validacao()
    validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())

    assert adapter.upsert_calls == []
    assert adapter.deleted_ids == []
    assert adapter.ensure_ready_calls == 0
    assert "ensure_ready" not in adapter.calls


def test_ac_015_modulo_e_chamavel_sem_linha_de_comando(tmp_path):
    # SPECSFY: US-003 FR-007 AC-015
    config = _base(tmp_path, consultas=GABARITO_OK)
    adapter = RecordingAdapter(
        {"a", "b"},
        results=[_resultado("plano de 500 Mega", "regulamento.md", 0.2)],
    )

    validacao = _validacao()
    report = validacao.validate_base(config, adapter=adapter, embeddings=StubEmbeddings())
    gravado = json.loads(Path(report.report_path).read_text(encoding="utf-8"))

    assert report.to_dict() == gravado


def test_load_query_cases_exige_criterio_declarado(tmp_path):
    # SPECSFY: FR-004 AC-004
    caminho = tmp_path / "consultas.yaml"
    caminho.write_text(
        '- pergunta: "Sem critério"\n  categoria: ampla\n', encoding="utf-8"
    )

    validacao = _validacao()

    with pytest.raises(ValueError):
        validacao.load_query_cases(str(caminho))
