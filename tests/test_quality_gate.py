"""Testes TDD da SPEC-0006 — gate de qualidade de chunks e metadados.

Arquivo próprio da fatia. Os marcadores ``SPECSFY:`` não declaram a spec de
origem e os IDs se repetem entre specs, então isolar a fatia em um arquivo é a
mitigação vigente para a contagem de cobertura, conforme a seção 11 da spec.

O Gherkin da seção 6 é a referência de comportamento; nenhum arquivo
``.feature`` é criado ou executado aqui.

Contrato definido por estes casos e materializado pelas tarefas T017 a T024:

``src.pipeline.quality``
    ``evaluate_quality(chunks, chunking_cfg, quality_cfg, *, manifest=None,
    output_dir=None) -> QualityReport``. Levanta ``QualityGateError`` quando um
    dos seis invariantes críticos falha, com a mensagem nomeando o invariante.
    ``QualityReport`` expõe ``desfecho``, ``impedimento``, ``documentos``,
    ``sinais``, ``limiares_aplicados``, ``avisos``, ``report_path``, ``render()``
    e ``to_dict()``.
    ``MINIMO_UTIL_PADRAO`` vale 60.

``quality`` (CLI na raiz)
    ``main(argv) -> int`` devolve 0 aprovado, 1 reprovado e 2 não avaliável.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

RAIZ = Path(__file__).resolve().parent.parent

METADADOS_OBRIGATORIOS = (
    "document_id",
    "source_hash",
    "project_id",
    "chunk_hash",
    "chunk_type",
)

SDKS_DE_BANCO_VETORIAL = (
    "qdrant_client",
    "chromadb",
    "pinecone",
    "langchain_qdrant",
    "langchain_chroma",
    "langchain_pinecone",
)

IDENTIFICADORES_DE_CLIENTE = (
    "vivo",
    "c6 bank",
    "cinemark",
    "banda larga",
    "cheque especial",
)


def _quality():
    """Import tardio do módulo em construção.

    Mantém o RED isolado em cada caso: sem isto o módulo ausente quebraria a
    coleta e apagaria o sinal de regressão do restante da suíte.
    """
    import src.pipeline.quality as modulo

    return modulo


def _cli():
    """Import tardio da CLI de diagnóstico em construção."""
    import quality as modulo

    return modulo


def _chunk(
    *,
    conteudo: str = "corpo do chunk com texto suficiente para não ser curto.",
    breadcrumb: str = "[Titulo > Secao]",
    documento: str = "base/a.md",
    chunk_id: str = "chunk-1",
    secao: str = "Secao",
    subsecao: str = "Subsecao",
    **extra,
) -> Document:
    """Constrói um chunk íntegro; cada caso remove só o que quer provar."""
    metadata = {
        "chunk_id": chunk_id,
        "document_id": "doc-1",
        "source_hash": "hash-fonte",
        "project_id": "projeto",
        "chunk_hash": f"hash-{chunk_id}",
        "chunk_type": "detail",
        "nome_arquivo": Path(documento).name,
        "caminho_relativo": documento,
        "titulo": "Titulo",
        "secao": secao,
        "subsecao": subsecao,
        "breadcrumb": breadcrumb,
        "chunk_index": 0,
        "total_chunks": 1,
    }
    metadata.update(extra)
    return Document(page_content=f"{breadcrumb}\n\n{conteudo}", metadata=metadata)


CHUNKING = {"default_chunk_size": 1000, "default_chunk_overlap": 200}
QUALIDADE = {"minimo_util": 60}


def test_chunk_sem_identidade_bloqueia_a_indexacao() -> None:
    # SPECSFY: US-001 FR-001 NFR-001 AC-001
    quality = _quality()
    chunks = [_chunk(), _chunk(chunk_id="")]

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality(chunks, CHUNKING, QUALIDADE)

    assert "chunk_id" in str(excinfo.value)


def test_identidade_duplicada_bloqueia_a_indexacao() -> None:
    # SPECSFY: US-001 FR-001 AC-002
    quality = _quality()
    chunks = [_chunk(chunk_id="repetido"), _chunk(chunk_id="repetido")]

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality(chunks, CHUNKING, QUALIDADE)

    assert "duplicad" in str(excinfo.value).lower()


def test_chunk_sem_conteudo_alem_do_breadcrumb_bloqueia_a_indexacao() -> None:
    # SPECSFY: US-001 FR-001 AC-003
    quality = _quality()
    vazio = Document(
        page_content="[Titulo > Secao]",
        metadata=dict(_chunk(chunk_id="vazio").metadata),
    )

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality([_chunk(), vazio], CHUNKING, QUALIDADE)

    assert "conteúdo" in str(excinfo.value).lower()


@pytest.mark.parametrize("metadado", METADADOS_OBRIGATORIOS)
def test_metadado_de_rastreabilidade_ausente_bloqueia_a_indexacao(metadado: str) -> None:
    # SPECSFY: US-001 FR-001 AC-004
    quality = _quality()
    incompleto = _chunk(chunk_id="incompleto")
    del incompleto.metadata[metadado]

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality([_chunk(), incompleto], CHUNKING, QUALIDADE)

    assert metadado in str(excinfo.value)


def test_truncamento_no_meio_da_frase_e_sinal_e_nao_bloqueia() -> None:
    # SPECSFY: US-001 FR-002 NFR-001 AC-005
    quality = _quality()
    truncado = _chunk(
        chunk_id="truncado",
        conteudo="A adesão ao Club Fan não tem custo para o",
    )

    report = quality.evaluate_quality([_chunk(), truncado], CHUNKING, QUALIDADE)

    assert report.desfecho == "aprovado"
    assert report.impedimento is None
    assert any("trunca" in sinal.lower() for sinal in report.sinais)


def test_duplicata_exata_e_sinal_e_identifica_o_documento() -> None:
    # SPECSFY: US-002 FR-002 AC-006
    quality = _quality()
    texto = "Saiba mais sobre este benefício consultando seu Regulamento."
    a = _chunk(chunk_id="dup-a", conteudo=texto, documento="base/regulamento.md")
    b = _chunk(chunk_id="dup-b", conteudo=texto, documento="base/regulamento.md")
    b.metadata["chunk_hash"] = a.metadata["chunk_hash"]

    report = quality.evaluate_quality([a, b], CHUNKING, QUALIDADE)

    assert report.desfecho == "aprovado"
    duplicata = report.sinais["duplicata_exata"]
    assert duplicata["base/regulamento.md"] == 2


def test_minimo_e_medido_sobre_o_conteudo_util_e_nao_sobre_o_bruto() -> None:
    # SPECSFY: US-002 FR-003 NFR-003 AC-007
    quality = _quality()
    breadcrumb = "[Aplicativos e Conteudos Incluidos > Musica > Apple Music]"
    assert len(breadcrumb) == 58
    curto = _chunk(
        chunk_id="curto",
        breadcrumb=breadcrumb,
        conteudo="### Apple Music - 30 dias gratis.",
    )
    assert len(curto.page_content) > 90

    report = quality.evaluate_quality([curto], CHUNKING, {"minimo_util": 60})

    assert report.sinais["conteudo_util_curto"]["base/a.md"] == 1
    assert report.limiares_aplicados["minimo_util"] == 60


def test_maximo_deriva_do_chunk_size_declarado_pelo_documento() -> None:
    # SPECSFY: US-002 FR-003 AC-008
    quality = _quality()
    grande = _chunk(
        chunk_id="grande",
        conteudo="x" * 1500,
        chunk_size_recommended=2000,
    )

    report = quality.evaluate_quality([grande], CHUNKING, QUALIDADE)

    assert report.sinais["tamanho_acima_do_maximo"] == {}
    assert report.documentos["base/a.md"]["maximo_derivado"] > 2000


def test_relatorio_agrupa_por_documento_e_poupa_os_saudaveis() -> None:
    # SPECSFY: US-002 FR-002 FR-004 NFR-003 AC-009
    quality = _quality()
    chunks = [
        _chunk(chunk_id="d1", documento="base/quebrado.md", secao="", subsecao=""),
        _chunk(chunk_id="d2", documento="base/quebrado.md", secao="", subsecao=""),
        _chunk(chunk_id="s1", documento="base/saudavel.md"),
    ]

    report = quality.evaluate_quality(chunks, CHUNKING, QUALIDADE)

    assert report.documentos["base/quebrado.md"]["sem_secao"] == 2
    assert report.documentos["base/saudavel.md"]["sem_secao"] == 0
    assert "base/quebrado.md" in report.render()


def test_resultado_estruturado_vai_para_arquivo_proprio_da_execucao(tmp_path: Path) -> None:
    # SPECSFY: US-002 FR-004 NFR-002 AC-010
    quality = _quality()

    report = quality.evaluate_quality(
        [_chunk()], CHUNKING, QUALIDADE, output_dir=tmp_path
    )

    destino = Path(report.report_path)
    assert destino.parent == tmp_path
    assert destino.name.startswith("quality-") and destino.suffix == ".json"
    conteudo = json.loads(destino.read_text(encoding="utf-8"))
    assert conteudo["desfecho"] == "aprovado"
    assert "chunks" in conteudo
    assert not (tmp_path / "manifest.json").exists()


def test_diagnostico_nao_abre_conexao_com_o_vector_store(tmp_path: Path) -> None:
    # SPECSFY: US-003 FR-005 NFR-001 AC-011
    quality = _quality()
    origem = ast.parse(Path(quality.__file__).read_text(encoding="utf-8"))
    importados = {
        no.module.split(".")[0]
        for no in ast.walk(origem)
        if isinstance(no, ast.ImportFrom) and no.module
    } | {
        alias.name.split(".")[0]
        for no in ast.walk(origem)
        if isinstance(no, ast.Import)
        for alias in no.names
    }
    assert not importados & set(SDKS_DE_BANCO_VETORIAL)

    arquivo = tmp_path / "chunks.json"
    arquivo.write_text(
        json.dumps([{"content": "[T > S]\n\ncorpo com texto suficiente.",
                     "metadata": dict(_chunk().metadata)}]),
        encoding="utf-8",
    )
    assert _cli().main(["--chunks", str(arquivo), "--output-dir", str(tmp_path)]) == 0


@pytest.mark.parametrize(
    ("condicao", "codigo"),
    [("integro", 0), ("invariante_violado", 1), ("nao_avaliavel", 2)],
)
def test_codigos_de_saida_do_diagnostico(
    condicao: str, codigo: int, tmp_path: Path
) -> None:
    # SPECSFY: US-003 FR-005 AC-012
    arquivo = tmp_path / "chunks.json"
    if condicao == "integro":
        entradas = [{"content": "[T > S]\n\ncorpo com texto suficiente.",
                     "metadata": dict(_chunk().metadata)}]
        arquivo.write_text(json.dumps(entradas), encoding="utf-8")
    elif condicao == "invariante_violado":
        metadata = dict(_chunk().metadata)
        metadata["chunk_id"] = ""
        arquivo.write_text(
            json.dumps([{"content": "[T > S]\n\ncorpo.", "metadata": metadata}]),
            encoding="utf-8",
        )

    resultado = _cli().main(["--chunks", str(arquivo), "--output-dir", str(tmp_path)])

    assert resultado == codigo


def test_saida_nao_expoe_credencial_nem_destino_remoto(tmp_path: Path) -> None:
    # SPECSFY: FR-004 NFR-002 AC-013
    quality = _quality()
    segredo = "sk-fake-credencial-de-teste"
    destino = "https://destino-remoto-ficticio.example.com"

    report = quality.evaluate_quality(
        [_chunk()],
        CHUNKING,
        {**QUALIDADE, "api_key": segredo, "url": destino},
        output_dir=tmp_path,
    )

    legivel = report.render()
    estruturado = Path(report.report_path).read_text(encoding="utf-8")
    for valor in (segredo, destino):
        assert valor not in legivel
        assert valor not in estruturado


def test_modulo_e_cli_ficam_livres_de_identidade_de_cliente() -> None:
    # SPECSFY: FR-003 NFR-003 AC-014
    for caminho in (
        RAIZ / "src" / "pipeline" / "quality.py",
        RAIZ / "quality.py",
    ):
        assert caminho.exists(), f"arquivo ausente: {caminho}"
        texto = caminho.read_text(encoding="utf-8").lower()
        for identificador in IDENTIFICADORES_DE_CLIENTE:
            assert identificador not in texto, f"{caminho.name} cita {identificador}"


def test_falha_de_gravacao_preserva_o_relatorio_e_o_desfecho(tmp_path: Path) -> None:
    # SPECSFY: US-003 FR-004 FR-005 NFR-002 AC-015
    quality = _quality()
    bloqueado = tmp_path / "somente-arquivo"
    bloqueado.write_text("ocupa o caminho como arquivo", encoding="utf-8")

    report = quality.evaluate_quality(
        [_chunk()], CHUNKING, QUALIDADE, output_dir=bloqueado
    )

    assert report.desfecho == "aprovado"
    assert report.report_path is None
    assert any("grav" in aviso.lower() for aviso in report.avisos)
    assert report.render()


def test_invariante_de_contagem_e_pulado_sem_manifesto() -> None:
    # SPECSFY: US-003 FR-001 FR-005 AC-016
    quality = _quality()

    report = quality.evaluate_quality([_chunk()], CHUNKING, QUALIDADE, manifest=None)

    assert report.desfecho == "aprovado"
    assert "contagem_do_manifesto" in report.invariantes_pulados
    assert len(report.invariantes_avaliados) == 5
    assert any("manifesto" in aviso.lower() for aviso in report.avisos)


def test_conjunto_vazio_bloqueia_a_indexacao() -> None:
    # SPECSFY: US-001 FR-001
    # Sem cenário BDD próprio: a seção 6 cobre quatro dos seis invariantes
    # críticos declarados por FR-001. Este caso e o seguinte fecham a lacuna
    # exigida pela Definition of Done, que pede um teste por invariante.
    quality = _quality()

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality([], CHUNKING, QUALIDADE)

    assert "nenhum chunk" in str(excinfo.value).lower()


def test_contagem_do_manifesto_inconsistente_bloqueia_a_indexacao() -> None:
    # SPECSFY: US-001 FR-001 FR-005
    quality = _quality()
    manifesto = {"chunk_count": 7}

    with pytest.raises(quality.QualityGateError) as excinfo:
        quality.evaluate_quality(
            [_chunk()], CHUNKING, QUALIDADE, manifest=manifesto
        )

    assert "contagem" in str(excinfo.value).lower()


def test_texto_colapsado_por_tabulacao_e_sinalizado() -> None:
    # SPECSFY: US-002 FR-002
    # Sexto sinal de FR-002, sem cenário BDD próprio na seção 6.
    quality = _quality()
    colado = _chunk(
        chunk_id="colado",
        conteudo="SaibamaissobreestebenefícioconsultandoseuRegulamento aqui.",
    )

    report = quality.evaluate_quality([_chunk(), colado], CHUNKING, QUALIDADE)

    assert report.desfecho == "aprovado"
    assert report.sinais["texto_colapsado"]["base/a.md"] == 1


def test_chunk_acima_do_maximo_derivado_e_sinalizado() -> None:
    # SPECSFY: US-002 FR-003
    # Caso positivo do sinal de tamanho: AC-008 prova apenas que um documento
    # com chunk_size maior no frontmatter não é sinalizado.
    quality = _quality()
    enorme = _chunk(chunk_id="enorme", conteudo="x" * 3000)

    report = quality.evaluate_quality([enorme], CHUNKING, QUALIDADE)

    assert report.desfecho == "aprovado"
    assert report.sinais["tamanho_acima_do_maximo"]["base/a.md"] == 1


def test_gate_nao_altera_a_estrutura_do_manifesto() -> None:
    # SPECSFY: US-002 FR-004
    from src.pipeline.manifest import build_manifest

    quality = _quality()
    chunks = [_chunk()]
    manifesto = build_manifest(
        chunks,
        project_id="projeto",
        collection_name="colecao",
        embedding_cfg={"provider": "fake", "model": "m", "dimensions": 3},
    )
    antes = json.dumps(manifesto, sort_keys=True, ensure_ascii=False)

    quality.evaluate_quality(chunks, CHUNKING, QUALIDADE, manifest=manifesto)

    assert json.dumps(manifesto, sort_keys=True, ensure_ascii=False) == antes
