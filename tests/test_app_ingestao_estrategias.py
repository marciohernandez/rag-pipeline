"""Estratégias de divisão, resumos, qualidade e destino configurados pelo front (SPEC-0029).

Fase RED: a Prévia e a publicação só aceitam ``header`` e ``recursive``, não
conhecem o campo ``processamento`` e o envio não guarda resumos, qualidade nem
destino. Nenhum caso toca rede: storage é temporário e a fachada de
sincronização é substituída quando o worker roda.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from tests._conexoes import (
    OWNER,
    capturar_agendamento,
    cliente,
    contar,
    criar_conexao_ok,
    criar_workspace,
    descrever_colecao,
    payload_embeddings,
    payload_qdrant,
    publicar,
    storage_temporario,
)
from tests._pessoas import sessao_do_banco

SECAO_COM_QUATRO = (
    "# Manual\n\n## Planos\n\nIntrodução dos planos.\n\n"
    "### Básico\n\nTexto do plano básico.\n\n### Médio\n\nTexto do plano médio.\n\n"
    "### Avançado\n\nTexto do plano avançado.\n\n### Total\n\nTexto do plano total.\n"
)


def _md(nome: str, texto: str) -> tuple[str, tuple[str, bytes, str]]:
    return ("arquivos", (nome, texto.encode(), "text/markdown"))


def _previa(
    client,
    arquivos,
    *,
    splitter="header",
    chunk_size=1000,
    chunk_overlap=200,
    processamento=None,
    **extra,
):
    dados: dict[str, Any] = {
        "splitter": splitter,
        "chunk_size": str(chunk_size),
        "chunk_overlap": str(chunk_overlap),
        "tamanho_pagina": "100",
    }
    if processamento is not None:
        dados["processamento"] = json.dumps(processamento)
    dados.update({chave: str(valor) for chave, valor in extra.items()})
    return client.post("/api/v1/ingestao/previa", data=dados, files=arquivos, headers=OWNER)


def _textos(resposta) -> list[str]:
    assert resposta.status_code == 200, resposta.text
    return [item["texto"] for item in resposta.json()["chunks"]]


def _tipos(resposta) -> list[str]:
    assert resposta.status_code == 200, resposta.text
    return [item.get("tipo") for item in resposta.json()["chunks"]]


def _sem_resumos() -> dict:
    return {"resumos": {"ativo": False, "minimo_subsecoes": 3}}


def _executar_worker(agendamento: dict, monkeypatch) -> dict:
    """Roda o worker com a fachada falsa e devolve a configuração que ele montou."""
    from src.app import tasks

    capturado: dict = {}

    def run_pipeline(config, **kwargs):
        capturado["config"] = config
        return SimpleNamespace(chunks=[])

    monkeypatch.setattr("src.pipeline.service.run_pipeline", run_pipeline)
    monkeypatch.setattr(
        "src.pipeline.service.sync_documents",
        lambda config, chunks, on_document=None: SimpleNamespace(
            previstos=0, inseridos=0, mantidos=0, removidos=0
        ),
    )
    tasks.process_envio_task.func(agendamento["envio_id"])
    return capturado["config"]


def _preparar_publicacao(client, tmp_path, monkeypatch):
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    agendamentos = capturar_agendamento(monkeypatch)
    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant())
    return criar_workspace(client), embeddings["id"], qdrant["id"], agendamentos


def test_previa_divide_so_nos_niveis_de_cabecalho_escolhidos() -> None:
    """SPECSFY: SPEC-0029 US-001 US-002 FR-001 FR-004 AC-001"""
    client = cliente()
    texto = (
        "# Título\n\n## Seção A\n\nTexto A.\n\n### Sub A1\n\nTexto A1.\n\n## Seção B\n\nTexto B.\n"
    )
    processamento = {**_sem_resumos(), "opcoes": {"nivel_cabecalho": 2}}

    textos = _textos(
        _previa(client, [_md("doc.md", texto), _md("outro.md", texto)], processamento=processamento)
    )

    assert any(t.startswith("[Título > Seção A]") and "Sub A1" in t for t in textos)
    assert not any("> Sub A1]" in t for t in textos)


@pytest.mark.parametrize(
    ("splitter", "campos", "processamento"),
    [
        ("header", {"chunk_size": 400, "chunk_overlap": 0}, {"opcoes": {"nivel_cabecalho": 3}}),
        ("markdown", {"chunk_size": 400, "chunk_overlap": 0}, {"opcoes": {"nivel_cabecalho": 0}}),
        ("markdown_syntax", {}, {"opcoes": {"nivel_cabecalho": 3, "remover_cabecalhos": False}}),
        ("recursive", {"chunk_size": 400, "chunk_overlap": 0}, {}),
        (
            "character_split",
            {"chunk_size": 400, "chunk_overlap": 0},
            {"opcoes": {"separador": "\\n\\n"}},
        ),
        ("token", {"chunk_size": 50, "chunk_overlap": 0}, {"opcoes": {"encoding": "cl100k_base"}}),
    ],
)
def test_previa_aceita_as_seis_estrategias(splitter, campos, processamento) -> None:
    """SPECSFY: SPEC-0029 US-001 FR-001 FR-002 AC-002"""
    client = cliente()
    paragrafo = "Este é um parágrafo de teste com várias palavras para formar chunks. " * 8
    texto = f"# Guia\n\n## Parte um\n\n{paragrafo}\n\n## Parte dois\n\n{paragrafo}\n"

    textos = _textos(
        _previa(
            client,
            [_md("guia.md", texto)],
            splitter=splitter,
            processamento={**_sem_resumos(), **processamento},
            **campos,
        )
    )

    assert textos, f"a estratégia {splitter} não gerou chunks"
    if splitter == "token":
        import tiktoken

        codificador = tiktoken.get_encoding("cl100k_base")
        assert max(len(codificador.encode(t)) for t in textos) <= 50


@pytest.mark.parametrize(
    ("splitter", "campos", "processamento"),
    [
        ("header", {"chunk_size": 100}, {}),
        ("recursive", {"chunk_size": 1000, "chunk_overlap": 600}, {}),
        ("desconhecida", {}, {}),
        ("header", {}, {"opcoes": {"nivel_cabecalho": 7}}),
        ("header", {}, {"opcoes": {"nivel_cabecalho": 0}}),
        ("character_split", {}, {"opcoes": {"separador": ""}}),
        ("character_split", {}, {"opcoes": {"separador": "x" * 11}}),
        (
            "token",
            {"chunk_size": 3000, "chunk_overlap": 0},
            {"opcoes": {"encoding": "cl100k_base"}},
        ),
        ("token", {"chunk_size": 100, "chunk_overlap": 0}, {"opcoes": {"encoding": "latin1"}}),
    ],
)
def test_previa_recusa_parametros_de_divisao_invalidos(splitter, campos, processamento) -> None:
    """SPECSFY: SPEC-0029 US-001 FR-002 FR-003 AC-004"""
    client = cliente()

    resposta = _previa(
        client,
        [_md("doc.md", "# A\n\nTexto.")],
        splitter=splitter,
        processamento=processamento,
        **campos,
    )

    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["detail"]


def test_publicacao_guarda_escolhas_e_execucao_repete_a_previa(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0029 US-001 US-003 FR-003 FR-006 AC-005"""
    from src.app.models import Envio

    client = cliente()
    workspace, embeddings, qdrant, agendamentos = _preparar_publicacao(
        client, tmp_path, monkeypatch
    )
    processamento = {
        "opcoes": {"nivel_cabecalho": 0},
        "resumos": {"ativo": False, "minimo_subsecoes": 3},
        "destino": {"batch_size": 20},
    }

    resposta = publicar(
        client,
        workspace,
        embeddings,
        qdrant,
        splitter="markdown",
        chunk_size="800",
        chunk_overlap="100",
        processamento=json.dumps(processamento),
    )

    assert resposta.status_code == 201, resposta.text
    with sessao_do_banco() as sessao:
        envio = sessao.get(Envio, resposta.json()["envio_id"])
        assert envio.processamento["splitter"] == "markdown"
        assert envio.processamento["resumos"]["ativo"] is False
        assert envio.processamento["destino"] == {"batch_size": 20}
    from src.pipeline import service

    run_pipeline_real = service.run_pipeline
    configuracao = _executar_worker(agendamentos[0], monkeypatch)
    monkeypatch.setattr("src.pipeline.service.run_pipeline", run_pipeline_real)
    assert configuracao["chunking"]["default_splitter"] == "markdown"
    assert configuracao["chunking"]["default_chunk_size"] == 800
    assert configuracao["chunking"]["generate_section_summaries"] is False
    assert configuracao["embedding"]["batch_size"] == 20

    pasta = tmp_path / "comparacao"
    pasta.mkdir()
    texto = "# Documento\n\n## Seção A\n\nTexto da seção A.\n\n## Seção B\n\nTexto da seção B.\n"
    (pasta / "doc.md").write_text(texto, encoding="utf-8")
    da_execucao = service.preview_chunks(
        {
            **configuracao,
            "caminhos": {"input_dir": str(pasta), "chunks_file": str(pasta / "chunks.json")},
        },
        input_dir=str(pasta),
    )
    previa = _previa(
        client,
        [_md("doc.md", texto)],
        splitter="markdown",
        chunk_size=800,
        chunk_overlap=100,
        processamento=processamento,
    )
    assert previa.json()["resumo"]["chunks"] == len(da_execucao.chunks)


def test_envio_sem_processamento_repete_com_os_padroes_atuais(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0029 US-001 FR-003 NFR-002 AC-006"""
    client = cliente()
    workspace, embeddings, qdrant, agendamentos = _preparar_publicacao(
        client, tmp_path, monkeypatch
    )
    resposta = publicar(client, workspace, embeddings, qdrant)
    assert resposta.status_code == 201, resposta.text
    envio_id = resposta.json()["envio_id"]
    from src.app.models import Envio

    with sessao_do_banco() as sessao:
        envio = sessao.get(Envio, envio_id)
        envio.situacao = "failed"
        sessao.commit()

    repeticao = client.post(f"/api/v1/envios/{envio_id}/retry", headers=OWNER)
    assert repeticao.status_code == 202, repeticao.text
    configuracao = _executar_worker(agendamentos[-1], monkeypatch)

    chunking = configuracao["chunking"]
    assert chunking["default_splitter"] == "header"
    assert chunking["generate_section_summaries"] is True
    assert chunking["section_summary_min_children"] == 3
    assert chunking.get(
        "headers_to_split_on", [["#", "titulo"], ["##", "secao"], ["###", "subsecao"]]
    ) == [
        ["#", "titulo"],
        ["##", "secao"],
        ["###", "subsecao"],
    ]
    assert configuracao["embedding"].get("batch_size", 50) == 50
    assert configuracao["vector_store"].get("sync_mode", "append") == "append"


def test_frontmatter_prevalece_sobre_a_estrategia_do_formulario() -> None:
    """SPECSFY: SPEC-0029 FR-001 FR-003 NFR-002 AC-007"""
    client = cliente()
    qa = "---\nsplitter: qa\n---\nPergunta 1?\nResposta 1.\n++++\nPergunta 2?\nResposta 2.\n"
    caractere = "---\nsplitter: character\n---\n" + ("Linha de texto comum para dividir. " * 60)
    comum = "# Comum\n\n" + ("Texto comum para tokens. " * 30)

    resposta = _previa(
        client,
        [_md("qa.md", qa), _md("caractere.md", caractere), _md("comum.md", comum)],
        splitter="token",
        chunk_size=50,
        chunk_overlap=0,
        processamento={**_sem_resumos(), "opcoes": {"encoding": "cl100k_base"}},
    )

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert sorted(corpo["arquivos_com_configuracao_propria"]) == ["caractere.md", "qa.md"]
    assert sum(1 for item in corpo["chunks"] if item["documento"] == "qa.md") == 2
    # `character` continua recursivo por caracteres: o tamanho 50 vale como caracteres,
    # enquanto o arquivo comum é medido em tokens e gera chunks mais longos.
    do_caractere = [item for item in corpo["chunks"] if item["documento"] == "caractere.md"]
    do_comum = [item for item in corpo["chunks"] if item["documento"] == "comum.md"]
    assert len(do_caractere) > 1
    assert max(item["tamanho"] for item in do_caractere) <= 50
    assert max(item["tamanho"] for item in do_comum) > 50


def test_previa_sem_resumos_de_secao() -> None:
    """SPECSFY: SPEC-0029 US-002 FR-004 AC-008"""
    client = cliente()
    arquivos = [_md("manual.md", SECAO_COM_QUATRO)]

    ligado = _tipos(
        _previa(client, arquivos, processamento={"resumos": {"ativo": True, "minimo_subsecoes": 3}})
    )
    desligado = _tipos(_previa(client, arquivos, processamento=_sem_resumos()))

    assert "section_summary" in ligado
    assert "section_summary" not in desligado


def test_minimo_de_subsecoes_controla_os_resumos() -> None:
    """SPECSFY: SPEC-0029 US-002 FR-004 AC-009"""
    client = cliente()
    duas = "# Guia\n\n## Curta\n\n### Um\n\nTexto um.\n\n### Dois\n\nTexto dois.\n\n"
    texto = duas + SECAO_COM_QUATRO.replace("# Manual\n\n", "")
    arquivos = [_md("guia.md", texto)]
    resumos = {"resumos": {"ativo": True, "minimo_subsecoes": 2}}

    por_cabecalho = _tipos(_previa(client, arquivos, processamento=resumos))
    recursivo = _tipos(
        _previa(
            client,
            arquivos,
            splitter="recursive",
            chunk_size=400,
            chunk_overlap=0,
            processamento=resumos,
        )
    )

    assert por_cabecalho.count("section_summary") == 2
    assert recursivo.count("section_summary") == 0


def test_minimo_util_altera_os_avisos_da_previa() -> None:
    """SPECSFY: SPEC-0029 US-002 FR-005 AC-010"""
    client = cliente()
    texto = "# Curto\n\n## Item\n\n" + ("a" * 30) + ".\n"
    arquivos = [_md("curto.md", texto)]

    com_40 = _previa(
        client, arquivos, processamento={**_sem_resumos(), "qualidade": {"minimo_util": 40}}
    )
    com_60 = _previa(
        client, arquivos, processamento={**_sem_resumos(), "qualidade": {"minimo_util": 60}}
    )

    assert com_40.status_code == 200 and com_60.status_code == 200, (com_40.text, com_60.text)
    assert not any("conteúdo útil abaixo de" in aviso for aviso in com_40.json()["avisos"])
    assert any("conteúdo útil abaixo de 60" in aviso for aviso in com_60.json()["avisos"])


def test_status_bloqueado_exclui_documentos() -> None:
    """SPECSFY: SPEC-0029 US-002 FR-005 AC-011"""
    client = cliente()
    rascunho = "---\nstatus: rascunho\n---\n# Rascunho\n\nTexto em rascunho.\n"
    publicado = "# Publicado\n\nTexto publicado.\n"

    resposta = _previa(
        client,
        [_md("rascunho.md", rascunho), _md("publicado.md", publicado)],
        processamento={**_sem_resumos(), "contrato": {"status_bloqueado": ["rascunho"]}},
    )

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert {item["documento"] for item in corpo["chunks"]} == {"publicado.md"}
    assert corpo["documentos_excluidos"] == ["rascunho.md"]


@pytest.mark.parametrize(
    "processamento",
    [
        {"resumos": {"ativo": True, "minimo_subsecoes": 1}},
        {"resumos": {"ativo": True, "minimo_subsecoes": 11}},
        {"qualidade": {"minimo_util": -1}},
        {"qualidade": {"minimo_util": 1001}},
        {"contrato": {"status_bloqueado": [""]}},
        {"contrato": {"status_bloqueado": ["rascunho", "rascunho"]}},
        {"contrato": {"status_bloqueado": ["x" * 41]}},
        {"contrato": {"status_bloqueado": [f"s{i}" for i in range(21)]}},
    ],
)
def test_recusa_resumos_e_qualidade_invalidos(processamento) -> None:
    """SPECSFY: SPEC-0029 US-002 FR-004 FR-005 AC-012"""
    client = cliente()

    resposta = _previa(client, [_md("doc.md", "# A\n\nTexto.")], processamento=processamento)

    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["detail"]


def test_destino_escolhido_chega_ao_worker_e_a_repeticao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0029 US-003 FR-006 NFR-002 AC-014"""
    client = cliente()
    workspace, embeddings, qdrant, agendamentos = _preparar_publicacao(
        client, tmp_path, monkeypatch
    )

    resposta = publicar(
        client,
        workspace,
        embeddings,
        qdrant,
        processamento=json.dumps({"destino": {"batch_size": 20}}),
    )
    assert resposta.status_code == 201, resposta.text

    primeira = _executar_worker(agendamentos[0], monkeypatch)
    assert primeira["embedding"]["batch_size"] == 20
    assert "sync_mode" not in primeira["vector_store"]

    envio_id = resposta.json()["envio_id"]
    from src.app.models import Envio

    with sessao_do_banco() as sessao:
        sessao.get(Envio, envio_id).situacao = "failed"
        sessao.commit()
    repeticao = client.post(f"/api/v1/envios/{envio_id}/retry", headers=OWNER)
    assert repeticao.status_code == 202, repeticao.text
    segunda = _executar_worker(agendamentos[-1], monkeypatch)
    assert segunda["embedding"]["batch_size"] == 20
    assert "sync_mode" not in segunda["vector_store"]


@pytest.mark.parametrize(
    "destino",
    [
        {"batch_size": 0},
        {"batch_size": 501},
        {"batch_size": 50, "sync_mode": "append"},
        {"batch_size": 50, "sync_mode": "mirror"},
    ],
)
def test_publicacao_recusa_destino_invalido(destino, tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0029 US-003 FR-006 AC-015"""
    client = cliente()
    workspace, embeddings, qdrant, agendamentos = _preparar_publicacao(
        client, tmp_path, monkeypatch
    )
    envios_antes = contar("Envio")

    resposta = publicar(
        client, workspace, embeddings, qdrant, processamento=json.dumps({"destino": destino})
    )

    assert resposta.status_code == 422, resposta.text
    assert contar("Envio") == envios_antes
    assert agendamentos == []


def test_markdown_recursivo_divide_por_cabecalhos() -> None:
    """SPECSFY: SPEC-0029 US-001 FR-001 FR-002 FR-004 AC-027"""
    client = cliente()
    longo = "Frase longa de conteúdo para obrigar a divisão por tamanho. " * 12
    texto = "".join(
        f"{marca} {titulo}\n\n{longo}\n\n"
        for marca, titulo in (("#", "A"), ("##", "B"), ("###", "C"), ("####", "D"), ("#####", "E"))
    )
    arquivos = [_md("niveis.md", texto)]

    ate_h4 = _textos(
        _previa(
            client,
            arquivos,
            splitter="markdown",
            chunk_size=500,
            chunk_overlap=0,
            processamento={**_sem_resumos(), "opcoes": {"nivel_cabecalho": 4}},
        )
    )
    desativado = _textos(
        _previa(
            client,
            arquivos,
            splitter="markdown",
            chunk_size=500,
            chunk_overlap=0,
            processamento={**_sem_resumos(), "opcoes": {"nivel_cabecalho": 0}},
        )
    )

    def titulos(texto_chunk: str) -> int:
        corpo = texto_chunk.split("\n\n", 1)[-1] if texto_chunk.startswith("[") else texto_chunk
        return sum(
            1 for linha in corpo.splitlines() if linha.startswith(("# ", "## ", "### ", "#### "))
        )

    assert all(titulos(t) <= 1 for t in ate_h4)
    assert any(t.startswith("[A > B > C > D]") for t in ate_h4)
    assert all(len(t.split("\n\n", 1)[-1]) <= 500 for t in ate_h4)
    assert not any(t.startswith("[") for t in desativado)


def test_separador_personalizado_no_por_caractere() -> None:
    """SPECSFY: SPEC-0029 US-001 FR-002 AC-028"""
    client = cliente()
    blocos = "\n---\n".join(f"Bloco {i}: " + ("conteúdo do bloco " * 8) for i in range(6))
    arquivos = [_md("blocos.md", blocos)]

    textos = _textos(
        _previa(
            client,
            arquivos,
            splitter="character_split",
            chunk_size=300,
            chunk_overlap=0,
            processamento={**_sem_resumos(), "opcoes": {"separador": "\\n---\\n"}},
        )
    )
    vazio = _previa(
        client,
        arquivos,
        splitter="character_split",
        chunk_size=300,
        chunk_overlap=0,
        processamento={**_sem_resumos(), "opcoes": {"separador": ""}},
    )

    assert len(textos) >= 2
    assert not any("---" in t for t in textos)
    assert vazio.status_code == 422, vazio.text
