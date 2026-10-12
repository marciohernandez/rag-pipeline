"""Prévia descartável dos chunks (SPEC-0026, US-002).

Fase RED: `/api/v1/ingestao/padroes` e `/api/v1/ingestao/previa` ainda não
existem. Storage, vector store e embeddings são armadilhas: qualquer toque falha.
"""

from __future__ import annotations

import pytest

from tests._conexoes import MEMBER, OWNER, cliente, contar


class _Armadilha:
    """Falha o teste se alguém usar o destino que não deveria ser tocado."""

    def __getattr__(self, nome):
        raise AssertionError(f"a prévia não pode tocar em {nome}")


def _armar(monkeypatch) -> None:
    from src.app import storage as storage_module

    monkeypatch.setattr(storage_module, "_STORAGE", _Armadilha())
    monkeypatch.setattr(
        "src.pipeline.service.sync_vector_store",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("sem sincronização na prévia")),
    )


def _md(nome: str, texto: str) -> tuple[str, tuple[str, bytes, str]]:
    return ("arquivos", (nome, texto.encode(), "text/markdown"))


def _previa(client, arquivos, **campos):
    dados = {"splitter": "header", "chunk_size": "1000", "chunk_overlap": "200"}
    dados.update({chave: str(valor) for chave, valor in campos.items()})
    return client.post("/api/v1/ingestao/previa", data=dados, files=arquivos, headers=OWNER)


def test_previa_com_splitter_por_cabecalhos_sem_persistir(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-006 FR-007 NFR-003 AC-007"""
    client = cliente()
    _armar(monkeypatch)
    arquivos = [
        _md(f"doc-{i}.md", f"# Título {i}\n\n## Seção\n\nConteúdo útil do documento {i}.")
        for i in range(3)
    ]
    bases_antes = contar("Base")

    resposta = _previa(client, arquivos)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["resumo"]["documentos"] == 3
    assert corpo["resumo"]["chunks"] >= 3
    assert corpo["resumo"]["tamanho_medio"] > 0
    primeiro = corpo["chunks"][0]
    assert {"documento", "posicao", "tamanho", "texto"} <= set(primeiro)
    assert contar("Base") == bases_antes


def test_previa_respeita_frontmatter_e_avisa_os_arquivos_afetados(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-008"""
    client = cliente()
    _armar(monkeypatch)
    qa = "---\nsplitter: qa\n---\nP: Um?\nR: Um.\n\n++++\n\nP: Dois?\nR: Dois."
    proprio = "---\nchunk_size_recommended: 300\n---\n# Longo\n\n" + ("palavra " * 200)
    comum = "# Comum\n\nTexto comum curto."
    arquivos = [_md("qa.md", qa), _md("proprio.md", proprio), _md("comum.md", comum)]

    resposta = _previa(client, arquivos, splitter="recursive", chunk_size=500, chunk_overlap=50)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert sorted(corpo["arquivos_com_configuracao_propria"]) == ["proprio.md", "qa.md"]
    chunks_qa = [c for c in corpo["chunks"] if c["documento"] == "qa.md"]
    assert len(chunks_qa) == 2


@pytest.mark.parametrize(
    "campos",
    [
        {"chunk_size": 500, "chunk_overlap": 500},
        {"chunk_size": 100, "chunk_overlap": 0},
        {"chunk_size": 5000, "chunk_overlap": 0},
        {"chunk_size": 1000, "chunk_overlap": 600},
        {"splitter": "desconhecido"},
    ],
)
def test_previa_recusa_parametros_fora_dos_limites(monkeypatch, campos) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009"""
    client = cliente()
    _armar(monkeypatch)

    resposta = _previa(client, [_md("a.md", "# A\n\nTexto.")], **campos)

    assert resposta.status_code in {400, 422}, resposta.text


def test_previa_recusa_arquivos_invalidos_e_acima_do_limite(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009"""
    client = cliente()
    _armar(monkeypatch)
    grande = ("arquivos", ("grande.md", b"a" * (5 * 1024 * 1024 + 1), "text/markdown"))
    muitos = [_md(f"d{i}.md", "# D\n\nTexto.") for i in range(51)]

    respostas = [
        _previa(client, [("arquivos", ("nota.txt", b"texto", "text/plain"))]),
        _previa(client, [grande]),
        _previa(client, muitos),
    ]

    assert [r.status_code for r in respostas] == [400, 400, 400]


def test_member_nao_calcula_previa(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009"""
    client = cliente()
    _armar(monkeypatch)

    resposta = client.post(
        "/api/v1/ingestao/previa",
        data={"splitter": "header", "chunk_size": "1000", "chunk_overlap": "200"},
        files=[_md("a.md", "# A\n\nTexto.")],
        headers=MEMBER,
    )

    assert resposta.status_code == 403, resposta.text
