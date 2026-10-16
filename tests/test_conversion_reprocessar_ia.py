"""Selo "revisar" geral e reprocessamento com IA sob pedido (SPEC-0036, US-005)."""

from __future__ import annotations

import io

from docx import Document

from tests._fase1_conversao import (
    AUTH_MEMBER,
    AUTH_OWNER,
    armazenamento_temporario,
    cliente,
    criar_lote,
    executar,
    exigir,
    ler_documento,
    ler_markdown,
    sem_enfileirar,
)


def _docx(texto: str) -> bytes:
    documento = Document()
    documento.add_paragraph(texto)
    saida = io.BytesIO()
    documento.save(saida)
    return saida.getvalue()


def _proibir_ia(monkeypatch, chamadas: list):
    modulo = exigir("src.pipeline.conversion.reprocessar_ia")

    def _nunca(self, *args, **kwargs):
        chamadas.append(args)
        raise AssertionError("a IA não pode ser chamada sem pedido")

    monkeypatch.setattr(modulo.ReprocessadorIa, "reprocessar", _nunca)


def test_spec_0036_ac_019_baixa_qualidade_marca_revisar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-007 AC-019"""
    armazenamento_temporario(tmp_path, monkeypatch)
    _, ids = criar_lote([{"nome": "quase-vazio.docx", "formato": "docx", "conteudo": _docx("oi")}])

    executar(ids["quase-vazio.docx"])

    doc = ler_documento(ids["quase-vazio.docx"])
    assert doc.situacao == "concluido"
    assert [a["codigo"] for a in doc.avisos] == ["baixa_qualidade"]


def test_spec_0036_ac_020_documento_bom_nao_recebe_selo(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-007 NFR-005 AC-020"""
    qualidade = exigir("src.pipeline.conversion.qualidade")
    from src.pipeline.conversion.config import ConversaoConfig

    texto = "Texto corrido e legível com informação suficiente para indexar. " * 5
    assert qualidade.avaliar_qualidade(texto, ConversaoConfig()) == []
    avisos = qualidade.avaliar_qualidade("texto ������" * 3, ConversaoConfig())
    assert [a.codigo for a in avisos] == ["baixa_qualidade"]


def test_spec_0036_ac_021_reprocessar_envia_so_aquele_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-021"""
    from src.app import tasks
    from src.app.storage import get_storage
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    sem_enfileirar(monkeypatch)
    modulo = exigir("src.pipeline.conversion.reprocessar_ia")
    chamadas: list[str] = []
    monkeypatch.setattr(
        modulo.ReprocessadorIa,
        "reprocessar",
        lambda self, caminho, formato: chamadas.append(caminho.name) or "# Texto melhorado pela IA",
    )
    reprocessos: list[str] = []
    monkeypatch.setattr(
        tasks.reprocessar_documento_ia_task,
        "defer",
        lambda **kw: reprocessos.append(kw["documento_id"]),
    )
    lote_id, ids = criar_lote(
        [
            {"nome": "a.docx", "formato": "docx", "conteudo": _docx("oi"), "situacao": "concluido"},
            {"nome": "b.docx", "formato": "docx", "conteudo": _docx("oi"), "situacao": "concluido"},
        ]
    )
    _criar_workspace(c)

    resposta = c.post(
        f"/api/v1/conversoes/{lote_id}/documentos/{ids['a.docx']}/reprocessar-ia",
        headers=AUTH_OWNER,
    )

    assert resposta.status_code == 202
    assert reprocessos == [ids["a.docx"]]
    tasks.reprocessar_documento_ia_task.func(documento_id=ids["a.docx"])
    assert chamadas == ["a.docx"]
    assert [a["codigo"] for a in ler_documento(ids["a.docx"]).avisos] == ["baixa_qualidade"]
    assert "Texto melhorado pela IA" in ler_markdown(get_storage(), ids["a.docx"], "a.md", tmp_path)


def test_spec_0036_ac_022_sem_pedido_nada_vai_a_ia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-008 FR-009 NFR-002 AC-022"""
    armazenamento_temporario(tmp_path, monkeypatch)
    chamadas: list = []
    _proibir_ia(monkeypatch, chamadas)
    _, ids = criar_lote(
        [
            {"nome": "r1.docx", "formato": "docx", "conteudo": _docx("oi")},
            {"nome": "r2.docx", "formato": "docx", "conteudo": _docx("ok")},
        ]
    )

    for documento_id in ids.values():
        executar(documento_id)

    assert chamadas == []
    assert all(ler_documento(i).situacao == "concluido" for i in ids.values())


def test_spec_0036_ac_023_falha_da_ia_preserva_o_markdown_anterior(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-008 AC-023"""
    from src.app import tasks
    from src.app.storage import get_storage

    storage = armazenamento_temporario(tmp_path, monkeypatch)
    modulo = exigir("src.pipeline.conversion.reprocessar_ia")

    def _falha(self, caminho, formato):
        raise RuntimeError("provedor caiu: chave sk-secreta")

    monkeypatch.setattr(modulo.ReprocessadorIa, "reprocessar", _falha)
    _, ids = criar_lote([{"nome": "a.docx", "formato": "docx", "conteudo": _docx("oi")}])
    executar(ids["a.docx"])
    antes = ler_markdown(storage, ids["a.docx"], "a.md", tmp_path)

    # Simula o estado enfileirado por um pedido explícito, como no endpoint.
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao

    with SessionLocal() as session:
        session.get(DocumentoConversao, ids["a.docx"]).situacao = "processando"
        session.commit()
    tasks.reprocessar_documento_ia_task.func(documento_id=ids["a.docx"])

    doc = ler_documento(ids["a.docx"])
    assert doc.situacao == "concluido"
    assert "sk-secreta" not in (doc.erro or "")
    assert doc.erro
    assert ler_markdown(get_storage(), ids["a.docx"], "a.md", tmp_path / "depois") == antes


def test_spec_0036_ac_024_member_nao_reprocessa_com_ia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-024"""
    c = cliente(tmp_path, monkeypatch)
    chamadas: list = []
    _proibir_ia(monkeypatch, chamadas)
    lote_id, ids = criar_lote(
        [{"nome": "a.docx", "formato": "docx", "conteudo": _docx("oi"), "situacao": "concluido"}]
    )

    resposta = c.post(
        f"/api/v1/conversoes/{lote_id}/documentos/{ids['a.docx']}/reprocessar-ia",
        headers=AUTH_MEMBER,
    )

    assert resposta.status_code == 403
    assert chamadas == []


def test_spec_0036_job_repetido_nao_reenvia_conteudo_sem_novo_pedido(tmp_path, monkeypatch):
    """SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-022"""
    from src.app import tasks

    armazenamento_temporario(tmp_path, monkeypatch)
    chamadas = []
    _proibir_ia(monkeypatch, chamadas)
    _, ids = criar_lote(
        [{"nome": "a.docx", "formato": "docx", "conteudo": _docx("oi"), "situacao": "concluido"}]
    )
    tasks.reprocessar_documento_ia_task.func(documento_id=ids["a.docx"])
    assert chamadas == []
