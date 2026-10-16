"""Testes da tarefa assíncrona de conversão de documentos (SPEC-0023)."""

from __future__ import annotations

import logging
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"


def test_spec_0023_ac_002_falha_parcial_nao_interrompe_o_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-002 US-004 FR-002 FR-004 FR-006 NFR-003 AC-002"""
    from src.app import storage as storage_module
    from src.app import tasks as tasks_module
    from src.app.db import SessionLocal
    from src.app.main import app as _app  # noqa: F401 — configura banco e storage

    process_conversion_document_task = tasks_module.process_conversion_document_task

    from src.app.models import DocumentoConversao, LoteConversao, Workspace
    from src.app.storage import LocalDirectoryStorage

    raiz_storage = tmp_path / "uploads-spec-0023"
    storage = LocalDirectoryStorage(raiz_storage)
    monkeypatch.setattr(storage_module, "_STORAGE", storage)

    pdf_valido = (FIXTURES / "relatorio.pdf").read_bytes()
    documentos_entrada = [
        ("valido-a.pdf", pdf_valido),
        ("corrompido.pdf", b"%PDF-1.7\nconteudo truncado sem xref nem trailer"),
        ("valido-b.pdf", pdf_valido),
    ]

    with SessionLocal() as session:
        workspace = Workspace(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="Conversão com falha parcial",
        )
        session.add(workspace)
        session.flush()
        lote = LoteConversao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            situacao="processando",
        )
        session.add(lote)
        session.flush()

        ids_por_nome: dict[str, str] = {}
        for nome, conteudo in documentos_entrada:
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=nome,
                formato="pdf",
                tamanho_bytes=len(conteudo),
                situacao="fila",
            )
            session.add(documento)
            session.flush()
            storage.save(documento.id, nome, conteudo)
            ids_por_nome[nome] = documento.id
        session.commit()
        lote_id = lote.id

    for documento_id in ids_por_nome.values():
        process_conversion_document_task.func(documento_id=documento_id)

    with SessionLocal() as session:
        lote_atual = session.get(LoteConversao, lote_id)
        documentos = {
            documento.nome_arquivo: documento
            for documento in session.query(DocumentoConversao)
            .filter_by(lote_id=lote_id)
            .all()
        }

        assert lote_atual is not None
        # SPEC-0037: sem domínio confirmado, o lote convertido aguarda o domínio.
        assert lote_atual.situacao == "aguardando_dominio"
        assert documentos["valido-a.pdf"].situacao == "concluido"
        assert documentos["valido-b.pdf"].situacao == "concluido"

        falho = documentos["corrompido.pdf"]
        assert falho.situacao == "falhou"
        assert falho.erro
        mensagem_segura = falho.erro.lower()
        assert "traceback" not in mensagem_segura
        assert "pymupdf" not in mensagem_segura

    for nome in ("valido-a.pdf", "valido-b.pdf"):
        documento_id = ids_por_nome[nome]
        assert list((raiz_storage / documento_id).glob("*.md"))

    documento_falho_id = ids_por_nome["corrompido.pdf"]
    assert (raiz_storage / documento_falho_id / "corrompido.pdf").exists()


def test_spec_0023_ac_018_falha_expoe_mensagem_segura_e_loga_tipo_e_origem(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    """SPECSFY: SPEC-0023 NFR-003 AC-018"""
    from src.app import storage as storage_module
    from src.app import tasks as tasks_module
    from src.app.db import SessionLocal
    from src.app.main import app as _app  # noqa: F401 — configura banco e storage
    process_conversion_document_task = tasks_module.process_conversion_document_task

    from src.app.models import DocumentoConversao, LoteConversao, Workspace
    from src.app.storage import LocalDirectoryStorage
    from src.pipeline import service

    segredo_interno = "dsn=postgresql://usuario:senha@interno"

    def falhar_conversao(*_args, **_kwargs):
        raise RuntimeError(segredo_interno)

    monkeypatch.setattr(service, "convert_document", falhar_conversao)
    storage = LocalDirectoryStorage(tmp_path / "uploads-spec-0023")
    monkeypatch.setattr(storage_module, "_STORAGE", storage)

    with SessionLocal() as session:
        workspace = Workspace(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="Falha segura",
        )
        session.add(workspace)
        session.flush()
        lote = LoteConversao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            situacao="processando",
        )
        session.add(lote)
        session.flush()
        documento = DocumentoConversao(
            lote_id=lote.id,
            nome_arquivo="interno.pdf",
            formato="pdf",
            tamanho_bytes=20,
            situacao="fila",
        )
        session.add(documento)
        session.flush()
        documento_id = documento.id
        storage.save(documento_id, "interno.pdf", b"%PDF-1.7")
        session.commit()

    with caplog.at_level(logging.ERROR, logger="src.app.tasks"):
        process_conversion_document_task.func(documento_id=documento_id)

    with SessionLocal() as session:
        documento_atual = session.get(DocumentoConversao, documento_id)
        assert documento_atual is not None
        assert documento_atual.situacao == "falhou"
        mensagem = documento_atual.erro.lower()
        assert "não foi possível converter" in mensagem
        assert "runtimeerror" not in mensagem
        assert segredo_interno not in mensagem

    log = caplog.text.lower()
    assert "runtimeerror" in log
    assert "test_task_process_conversion_document.py" in log
    assert segredo_interno not in log


def _converter_pdfs(tmp_path, monkeypatch, pdfs: dict[str, Path]) -> tuple[str, dict[str, str]]:
    """Cria um lote com os PDFs dados, roda a tarefa em cada um e devolve (lote, ids)."""
    from src.app import storage as storage_module
    from src.app import tasks as tasks_module
    from src.app.db import SessionLocal
    from src.app.main import app as _app  # noqa: F401 — configura banco e storage
    from src.app.models import DocumentoConversao, LoteConversao, Workspace
    from src.app.storage import LocalDirectoryStorage

    storage = LocalDirectoryStorage(tmp_path / "uploads-spec-0033")
    monkeypatch.setattr(storage_module, "_STORAGE", storage)

    ids: dict[str, str] = {}
    with SessionLocal() as session:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="OCR de PDF")
        session.add(workspace)
        session.flush()
        lote = LoteConversao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            situacao="processando",
        )
        session.add(lote)
        session.flush()
        for nome, caminho in pdfs.items():
            conteudo = caminho.read_bytes()
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=nome,
                formato="pdf",
                tamanho_bytes=len(conteudo),
                situacao="fila",
            )
            session.add(documento)
            session.flush()
            storage.save(documento.id, nome, conteudo)
            ids[nome] = documento.id
        session.commit()
        lote_id = lote.id

    for documento_id in ids.values():
        tasks_module.process_conversion_document_task.func(documento_id=documento_id)
    return lote_id, ids


def test_spec_0033_ac_004_grava_avisos_do_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-003 FR-006 FR-008 AC-004"""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao
    from tests._pdfs_spec0033 import criar_pdf

    pdf = criar_pdf(tmp_path / "vazia.pdf", ["texto", "imagem:"])
    _lote_id, ids = _converter_pdfs(tmp_path, monkeypatch, {"vazia.pdf": pdf})

    with SessionLocal() as session:
        documento = session.get(DocumentoConversao, ids["vazia.pdf"])
        assert documento is not None
        assert documento.situacao == "concluido"
        assert [(a["codigo"], a["pagina"]) for a in documento.avisos] == [("ocr_pouco_texto", 2)]
        assert documento.avisos[0]["mensagem"]


def test_spec_0033_ac_011_falha_de_ocr_nao_afeta_o_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-007 NFR-002 NFR-003 AC-011"""
    import pymupdf4llm

    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao
    from tests._pdfs_spec0033 import criar_pdf

    original = pymupdf4llm.to_markdown

    def ocr_quebrado(*args, **kwargs):
        if kwargs.get("use_ocr"):
            raise RuntimeError("falha simulada de OCR")
        return original(*args, **kwargs)

    monkeypatch.setattr(pymupdf4llm, "to_markdown", ocr_quebrado)
    pdf_ocr = criar_pdf(tmp_path / "imagem.pdf", ["imagem:Cláusula segunda"])
    pdf_texto = criar_pdf(tmp_path / "texto.pdf", ["texto"])

    lote_id, ids = _converter_pdfs(
        tmp_path, monkeypatch, {"imagem.pdf": pdf_ocr, "texto.pdf": pdf_texto}
    )

    with SessionLocal() as session:
        com_ocr = session.get(DocumentoConversao, ids["imagem.pdf"])
        so_texto = session.get(DocumentoConversao, ids["texto.pdf"])
        lote = session.get(LoteConversao, lote_id)
        assert com_ocr is not None and so_texto is not None and lote is not None
        assert so_texto.situacao == "concluido"
        assert so_texto.avisos == []
        assert com_ocr.situacao == "concluido"
        assert [a["codigo"] for a in com_ocr.avisos] == ["ocr_falhou"]
        # SPEC-0037: sem domínio confirmado, o lote convertido aguarda o domínio.
        assert lote.situacao == "aguardando_dominio"
