"""Testes de integração do fluxo de conversão de documentos (SPEC-0023)."""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"
AUTH_OWNER = {"Authorization": "Bearer pessoa-teste-owner"}
AUTH_MEMBER = {"Authorization": "Bearer pessoa-teste-member"}
AUTH_OUTRO_TENANT = {"Authorization": "Bearer pessoa-teste-outro-tenant"}


def _cliente_com_storage_temporario(tmp_path, monkeypatch) -> TestClient:
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.storage import LocalDirectoryStorage

    monkeypatch.setattr(
        storage_module,
        "_STORAGE",
        LocalDirectoryStorage(str(tmp_path / "uploads-spec-0023")),
    )
    return TestClient(app)


def _criar_workspace(client: TestClient) -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"nome": "Conversão de documentos"},
        headers=AUTH_OWNER,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _arquivos_reais() -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        (
            "arquivos",
            ("relatorio.pdf", (FIXTURES / "relatorio.pdf").read_bytes(), "application/pdf"),
        ),
        (
            "arquivos",
            (
                "planilha.xlsx",
                (FIXTURES / "planilha.xlsx").read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ),
        (
            "arquivos",
            ("imagem.jpg", (FIXTURES / "imagem.jpg").read_bytes(), "image/jpeg"),
        ),
    ]


def _assert_sem_lote_e_storage(tmp_path) -> None:
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao

    with SessionLocal() as session:
        assert session.query(LoteConversao).count() == 0
        assert session.query(DocumentoConversao).count() == 0
    assert not any((tmp_path / "uploads-spec-0023").rglob("*"))


def _persistir_lote_se_disponivel(
    workspace_id: str,
    *,
    situacao: str,
    documentos: list[dict[str, object]],
) -> tuple[str, dict[str, str], bool]:
    """Prepara estado real assim que os modelos da SPEC-0023 existirem."""
    try:
        from datetime import UTC, datetime, timedelta

        from src.app.db import SessionLocal
        from src.app.models import DocumentoConversao, LoteConversao
    except ImportError:
        return (
            "lote-conversao-ausente",
            {
                str(documento["nome_arquivo"]): f"documento-{indice}-ausente"
                for indice, documento in enumerate(documentos, start=1)
            },
            False,
        )

    agora = datetime.now(UTC)
    with SessionLocal() as session:
        lote = LoteConversao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace_id,
            situacao=situacao,
        )
        session.add(lote)
        session.flush()
        ids: dict[str, str] = {}
        for entrada in documentos:
            estado = str(entrada["situacao"])
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=str(entrada["nome_arquivo"]),
                formato=str(entrada.get("formato", "pdf")),
                tamanho_bytes=int(entrada.get("tamanho_bytes", 20)),
                situacao=estado,
                erro=entrada.get("erro"),
                concluido_em=entrada.get(
                    "concluido_em",
                    agora if estado in {"concluido", "falhou"} else None,
                ),
                expira_em=entrada.get(
                    "expira_em",
                    agora + timedelta(days=6)
                    if estado in {"concluido", "falhou"}
                    else None,
                ),
                apagado_em=entrada.get("apagado_em"),
            )
            session.add(documento)
            session.flush()
            ids[documento.nome_arquivo] = documento.id
        lote_id = lote.id
        session.commit()
    return lote_id, ids, True


def test_spec_0023_ac_001_converte_pdf_xlsx_jpg_sem_criar_base(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-001 US-002 US-003 FR-001 FR-002 FR-003 FR-004 FR-005 NFR-001 AC-001"""
    from src.app.db import SessionLocal
    from src.app.models import Base
    from src.app.tasks import process_conversion_document_task

    documentos_agendados: list[str] = []
    monkeypatch.setattr(
        process_conversion_document_task,
        "defer",
        lambda *, documento_id: documentos_agendados.append(documento_id),
    )
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)

    with SessionLocal() as session:
        bases_antes = session.query(Base).count()

    inicio = time.monotonic()
    envio = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=_arquivos_reais(),
        headers=AUTH_OWNER,
    )
    duracao = time.monotonic() - inicio

    assert envio.status_code == 201
    assert duracao < 5
    lote = envio.json()
    assert lote["situacao"] == "processando"
    assert {documento["formato"] for documento in lote["documentos"]} == {
        "pdf",
        "xlsx",
        "jpg",
    }
    assert {documento["situacao"] for documento in lote["documentos"]} == {"fila"}
    assert set(documentos_agendados) == {
        documento["id"] for documento in lote["documentos"]
    }

    for documento_id in documentos_agendados:
        process_conversion_document_task.func(documento_id=documento_id)

    for _ in range(3):
        acompanhamento = client.get(
            f"/api/v1/conversoes/{lote['id']}",
            headers=AUTH_OWNER,
        )
        assert acompanhamento.status_code == 200
        lote_atual = acompanhamento.json()
        if lote_atual["situacao"] == "concluido":
            break
    else:
        raise AssertionError("o lote não chegou à situação concluído durante o polling")

    assert {documento["situacao"] for documento in lote_atual["documentos"]} == {
        "concluido"
    }
    for documento in lote_atual["documentos"]:
        download = client.get(
            f"/api/v1/conversoes/{lote['id']}/documentos/{documento['id']}/markdown",
            headers=AUTH_OWNER,
        )
        assert download.status_code == 200
        assert download.content.strip()

    pacote = client.get(
        f"/api/v1/conversoes/{lote['id']}/pacote",
        headers=AUTH_OWNER,
    )
    assert pacote.status_code == 200
    with zipfile.ZipFile(io.BytesIO(pacote.content)) as arquivo_zip:
        nomes_markdown = arquivo_zip.namelist()
        assert len(nomes_markdown) == 3
        assert all(nome.endswith(".md") for nome in nomes_markdown)

    with SessionLocal() as session:
        assert session.query(Base).count() == bases_antes


def test_spec_0023_ac_004_rejeita_zip_sem_criar_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-001 FR-001 AC-004"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    conteudo_zip = io.BytesIO()
    with zipfile.ZipFile(conteudo_zip, "w") as arquivo_zip:
        arquivo_zip.writestr("documento.txt", "conteúdo não suportado")

    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            (
                "arquivos",
                ("documentos.zip", conteudo_zip.getvalue(), "application/zip"),
            )
        ],
        headers=AUTH_OWNER,
    )

    assert response.status_code == 400
    detalhe = response.json()["detail"].lower()
    assert "extensão" in detalhe
    assert "suport" in detalhe

    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao

    with SessionLocal() as session:
        assert session.query(LoteConversao).count() == 0
        assert session.query(DocumentoConversao).count() == 0
    assert not any((tmp_path / "uploads-spec-0023").rglob("*"))


def test_spec_0023_ac_005_rejeita_arquivo_acima_de_40_mb(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-001 AC-005"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)

    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            (
                "arquivos",
                ("grande.pdf", b"x" * (45 * 1024 * 1024), "application/pdf"),
            )
        ],
        headers=AUTH_OWNER,
    )

    assert response.status_code == 400
    assert "40 mb" in response.json()["detail"].lower()
    _assert_sem_lote_e_storage(tmp_path)


def test_spec_0023_ac_005_aceita_parte_do_lote_conforme_spec_0036(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0036 US-004 FR-006 NFR-005 AC-017 DEC-009."""
    from src.app.tasks import process_conversion_document_task

    monkeypatch.setattr(process_conversion_document_task, "defer", lambda **kw: None)
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    conteudo_26_mb = b"x" * (26 * 1024 * 1024)

    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            ("arquivos", ("parte-1.pdf", conteudo_26_mb, "application/pdf")),
            ("arquivos", ("parte-2.pdf", conteudo_26_mb, "application/pdf")),
        ],
        headers=AUTH_OWNER,
    )

    assert response.status_code == 201
    assert [d["nome_arquivo"] for d in response.json()["documentos"]] == ["parte-1.pdf"]
    assert [d["nome_arquivo"] for d in response.json()["recusados"]] == ["parte-2.pdf"]


def test_spec_0023_ac_005_rejeita_lote_acima_de_50_arquivos(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-001 AC-005"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)

    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            ("arquivos", (f"documento-{indice}.pdf", b"pdf", "application/pdf"))
            for indice in range(51)
        ],
        headers=AUTH_OWNER,
    )

    assert response.status_code == 400
    detalhe = response.json()["detail"].lower()
    assert "50" in detalhe
    assert "arquivo" in detalhe
    _assert_sem_lote_e_storage(tmp_path)


def test_spec_0023_ac_006_reenvia_somente_documento_falho(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-004 FR-002 FR-006 NFR-003 AC-006"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id = "lote-conversao-ausente"
    documento_falho_id = "documento-conversao-ausente"
    estado_persistido_disponivel = False

    try:
        from datetime import UTC, datetime, timedelta

        from src.app.db import SessionLocal
        from src.app.models import DocumentoConversao, LoteConversao
        from src.app.storage import get_storage
        from src.app.tasks import process_conversion_document_task
    except ImportError:
        # Os predecessores de produção ainda não existem no baseline RED. O
        # request abaixo mantém a primeira falha observável na rota ausente;
        # quando modelos e tarefa existirem, o mesmo caso usa persistência real.
        documentos_agendados: list[str] = []
    else:
        documentos_agendados = []
        monkeypatch.setattr(
            process_conversion_document_task,
            "defer",
            lambda *, documento_id: documentos_agendados.append(documento_id),
        )
        with SessionLocal() as session:
            lote = LoteConversao(
                tenant_id="tenant-1",
                project_id="projeto-1",
                workspace_id=workspace_id,
                situacao="concluido_com_falhas",
            )
            session.add(lote)
            session.flush()
            documento_falho = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo="corrompido.pdf",
                formato="pdf",
                tamanho_bytes=24,
                situacao="falhou",
                erro="Não foi possível converter o documento.",
                concluido_em=datetime.now(UTC),
                expira_em=datetime.now(UTC) + timedelta(days=6),
            )
            documento_concluido = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo="preservado.pdf",
                formato="pdf",
                tamanho_bytes=24,
                situacao="concluido",
                concluido_em=datetime.now(UTC),
                expira_em=datetime.now(UTC) + timedelta(days=6),
            )
            session.add_all([documento_falho, documento_concluido])
            session.flush()
            lote_id = lote.id
            documento_falho_id = documento_falho.id
            documento_concluido_id = documento_concluido.id
            session.commit()

        get_storage().save(documento_falho_id, "corrompido.pdf", b"pdf corrompido")
        estado_persistido_disponivel = True

    response = client.post(
        f"/api/v1/conversoes/{lote_id}/documentos/{documento_falho_id}/reenviar",
        headers=AUTH_OWNER,
    )

    assert response.status_code == 200
    assert response.json()["situacao"] == "fila"

    if estado_persistido_disponivel:
        with SessionLocal() as session:
            lote_atual = session.get(LoteConversao, lote_id)
            documento_falho_atual = session.get(
                DocumentoConversao,
                documento_falho_id,
            )
            documento_concluido_atual = session.get(
                DocumentoConversao,
                documento_concluido_id,
            )

            assert lote_atual is not None
            assert lote_atual.situacao == "processando"
            assert documento_falho_atual is not None
            assert documento_falho_atual.situacao == "fila"
            assert documento_falho_atual.erro is None
            assert documento_falho_atual.expira_em is None
            assert documento_concluido_atual is not None
            assert documento_concluido_atual.situacao == "concluido"
        assert documentos_agendados == [documento_falho_id]


def test_spec_0023_ac_007_baixa_pacote_apenas_com_markdown_concluido(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-003 FR-005 AC-007"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id = "lote-conversao-ausente"

    try:
        from datetime import UTC, datetime, timedelta

        from src.app.db import SessionLocal
        from src.app.models import DocumentoConversao, LoteConversao
        from src.app.storage import get_storage
    except ImportError:
        # O endpoint deve ser a primeira lacuna observável no baseline RED.
        # Quando os modelos existirem, o mesmo caso usa banco e Storage reais.
        pass
    else:
        agora = datetime.now(UTC)
        with SessionLocal() as session:
            lote = LoteConversao(
                tenant_id="tenant-1",
                project_id="projeto-1",
                workspace_id=workspace_id,
                situacao="concluido_com_falhas",
            )
            session.add(lote)
            session.flush()
            documentos = [
                DocumentoConversao(
                    lote_id=lote.id,
                    nome_arquivo="primeiro.pdf",
                    formato="pdf",
                    tamanho_bytes=20,
                    situacao="concluido",
                    concluido_em=agora,
                    expira_em=agora + timedelta(days=6),
                ),
                DocumentoConversao(
                    lote_id=lote.id,
                    nome_arquivo="segundo.xlsx",
                    formato="xlsx",
                    tamanho_bytes=20,
                    situacao="concluido",
                    concluido_em=agora,
                    expira_em=agora + timedelta(days=6),
                ),
                DocumentoConversao(
                    lote_id=lote.id,
                    nome_arquivo="falhou.pdf",
                    formato="pdf",
                    tamanho_bytes=20,
                    situacao="falhou",
                    erro="Não foi possível converter o documento.",
                    concluido_em=agora,
                    expira_em=agora + timedelta(days=6),
                ),
            ]
            session.add_all(documentos)
            session.flush()
            lote_id = lote.id
            ids_documentos = {documento.nome_arquivo: documento.id for documento in documentos}
            session.commit()

        storage = get_storage()
        storage.save(ids_documentos["primeiro.pdf"], "primeiro.md", b"# Primeiro\n")
        storage.save(ids_documentos["segundo.xlsx"], "segundo.md", b"# Segundo\n")
        storage.save(ids_documentos["falhou.pdf"], "falhou.pdf", b"pdf corrompido")

    response = client.get(
        f"/api/v1/conversoes/{lote_id}/pacote",
        headers=AUTH_OWNER,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    with zipfile.ZipFile(io.BytesIO(response.content)) as arquivo_zip:
        nomes = {Path(nome).name for nome in arquivo_zip.namelist()}
        assert nomes == {"primeiro.md", "segundo.md"}
        assert arquivo_zip.read("primeiro.md") == b"# Primeiro\n"
        assert arquivo_zip.read("segundo.md") == b"# Segundo\n"


def test_spec_0023_ac_008_baixa_markdown_individual_concluido(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-003 FR-005 AC-008"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id = "lote-conversao-ausente"
    documento_id = "documento-conversao-ausente"
    markdown_esperado = b"# Relatorio convertido\n\nConteudo preservado.\n"

    try:
        from datetime import UTC, datetime, timedelta

        from src.app.db import SessionLocal
        from src.app.models import DocumentoConversao, LoteConversao
        from src.app.storage import get_storage
    except ImportError:
        # O endpoint deve ser a primeira lacuna observável no baseline RED.
        # Quando os modelos existirem, o mesmo caso usa banco e Storage reais.
        pass
    else:
        agora = datetime.now(UTC)
        with SessionLocal() as session:
            lote = LoteConversao(
                tenant_id="tenant-1",
                project_id="projeto-1",
                workspace_id=workspace_id,
                situacao="concluido",
            )
            session.add(lote)
            session.flush()
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo="relatorio.pdf",
                formato="pdf",
                tamanho_bytes=20,
                situacao="concluido",
                concluido_em=agora,
                expira_em=agora + timedelta(days=6),
            )
            session.add(documento)
            session.flush()
            lote_id = lote.id
            documento_id = documento.id
            session.commit()

        get_storage().save(documento_id, "relatorio.md", markdown_esperado)

    response = client.get(
        f"/api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown",
        headers=AUTH_OWNER,
    )

    assert response.status_code == 200
    assert response.content == markdown_esperado
    assert "relatorio.md" in response.headers["content-disposition"]


def test_spec_0023_ac_009_outro_tenant_nao_consulta_nem_baixa_lote(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-008 NFR-002 AC-009"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, _, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido",
        documentos=[{"nome_arquivo": "privado.pdf", "situacao": "concluido"}],
    )

    resposta_dono = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OWNER,
    )
    consulta_externa = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OUTRO_TENANT,
    )
    pacote_externo = client.get(
        f"/api/v1/conversoes/{lote_id}/pacote",
        headers=AUTH_OUTRO_TENANT,
    )

    # Prova que o 404 externo vem do isolamento, não de uma rota inexistente.
    assert resposta_dono.status_code == 200
    assert consulta_externa.status_code == 404
    assert pacote_externo.status_code == 404


def test_spec_0023_ac_010_member_nao_envia_mas_visualiza_lotes(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-008 AC-010"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)

    envio = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[("arquivos", ("relatorio.pdf", b"%PDF-1.7", "application/pdf"))],
        headers=AUTH_MEMBER,
    )
    listagem = client.get(
        "/api/v1/conversoes",
        params={"workspace_id": workspace_id},
        headers=AUTH_MEMBER,
    )

    assert envio.status_code == 403
    assert "permiss" in envio.json()["detail"].lower()
    assert listagem.status_code == 200


def test_spec_0023_ac_011_consulta_situacao_do_lote_e_documentos(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-002 FR-004 AC-011"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, _, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="processando",
        documentos=[
            {"nome_arquivo": "aguardando.pdf", "situacao": "fila"},
            {"nome_arquivo": "convertendo.xlsx", "formato": "xlsx", "situacao": "processando"},
        ],
    )

    response = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OWNER,
    )

    assert response.status_code == 200
    lote = response.json()
    assert lote["situacao"] == "processando"
    assert {
        documento["nome_arquivo"]: documento["situacao"]
        for documento in lote["documentos"]
    } == {
        "aguardando.pdf": "fila",
        "convertendo.xlsx": "processando",
    }


def test_spec_0023_ac_015_download_expirado_orienta_reenvio(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-007 NFR-002 AC-015"""
    from datetime import UTC, datetime, timedelta

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    agora = datetime.now(UTC)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido",
        documentos=[
            {
                "nome_arquivo": "expirado.pdf",
                "situacao": "concluido",
                "concluido_em": agora - timedelta(days=8),
                "expira_em": agora - timedelta(days=1),
                "apagado_em": agora,
            }
        ],
    )

    response = client.get(
        f"/api/v1/conversoes/{lote_id}/documentos/{ids['expirado.pdf']}/markdown",
        headers=AUTH_OWNER,
    )

    assert response.status_code == 404
    detalhe = str(response.json()["detail"]).lower()
    assert "dispon" in detalhe
    assert "reenvi" in detalhe


def test_spec_0023_ac_016_falha_nao_bloqueia_downloads_concluidos(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-004 FR-006 AC-016"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, persistido = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido_com_falhas",
        documentos=[
            {"nome_arquivo": "primeiro.pdf", "situacao": "concluido"},
            {"nome_arquivo": "segundo.pdf", "situacao": "concluido"},
            {
                "nome_arquivo": "falhou.pdf",
                "situacao": "falhou",
                "erro": "Não foi possível converter o documento.",
            },
        ],
    )
    if persistido:
        from src.app.storage import get_storage

        get_storage().save(ids["primeiro.pdf"], "primeiro.md", b"# Primeiro\n")
        get_storage().save(ids["segundo.pdf"], "segundo.md", b"# Segundo\n")

    pacote = client.get(
        f"/api/v1/conversoes/{lote_id}/pacote",
        headers=AUTH_OWNER,
    )
    detalhe = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OWNER,
    )

    assert pacote.status_code == 200
    with zipfile.ZipFile(io.BytesIO(pacote.content)) as arquivo_zip:
        assert {Path(nome).name for nome in arquivo_zip.namelist()} == {
            "primeiro.md",
            "segundo.md",
        }
    assert detalhe.status_code == 200
    falho = next(
        documento
        for documento in detalhe.json()["documentos"]
        if documento["nome_arquivo"] == "falhou.pdf"
    )
    assert falho["situacao"] == "falhou"
    assert falho["erro"]


def test_spec_0023_ac_017_envio_de_50_documentos_retorna_em_fila(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 NFR-001 AC-017"""
    try:
        from src.app.tasks import process_conversion_document_task
    except ImportError:
        documentos_agendados: list[str] = []
    else:
        documentos_agendados = []
        monkeypatch.setattr(
            process_conversion_document_task,
            "defer",
            lambda *, documento_id: documentos_agendados.append(documento_id),
        )

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    inicio = time.monotonic()
    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            ("arquivos", (f"documento-{indice:02}.pdf", b"%PDF-1.7", "application/pdf"))
            for indice in range(50)
        ],
        headers=AUTH_OWNER,
    )
    duracao = time.monotonic() - inicio

    assert response.status_code == 201
    lote = response.json()
    assert duracao < 5
    assert len(lote["documentos"]) == 50
    assert {documento["situacao"] for documento in lote["documentos"]} == {"fila"}
    assert len(documentos_agendados) == 50


def test_spec_0023_ac_019_ids_de_outro_tenant_parecem_inexistentes(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-008 NFR-002 AC-019"""
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido",
        documentos=[{"nome_arquivo": "sigiloso.pdf", "situacao": "concluido"}],
    )
    documento_id = ids["sigiloso.pdf"]

    assert (
        client.get(f"/api/v1/conversoes/{lote_id}", headers=AUTH_OWNER).status_code
        == 200
    )
    detalhe_externo = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OUTRO_TENANT,
    )
    arquivo_externo = client.get(
        f"/api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown",
        headers=AUTH_OUTRO_TENANT,
    )

    assert detalhe_externo.status_code == 404
    assert arquivo_externo.status_code == 404


def _url_documento(lote_id: str, documento_id: str) -> str:
    return f"/api/v1/conversoes/{lote_id}/documentos/{documento_id}"


def test_spec_0023_ac_023_apaga_documento_e_recalcula_o_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-006 FR-010 NFR-002 AC-023"""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao
    from src.app.storage import get_storage

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido_com_falhas",
        documentos=[
            {"nome_arquivo": "bom.pdf", "situacao": "concluido"},
            {"nome_arquivo": "ruim.pdf", "situacao": "falhou", "erro": "ilegível"},
        ],
    )
    storage = get_storage()
    storage.save(ids["bom.pdf"], "bom.md", b"# Bom\n")
    storage.save(ids["ruim.pdf"], "ruim.pdf", b"original")

    apagado = client.delete(_url_documento(lote_id, ids["ruim.pdf"]), headers=AUTH_OWNER)

    assert apagado.status_code == 204
    assert storage.list_files(ids["ruim.pdf"]) == []
    assert storage.list_files(ids["bom.pdf"]) != []
    with SessionLocal() as session:
        assert session.get(DocumentoConversao, ids["ruim.pdf"]) is None
        assert session.get(DocumentoConversao, ids["bom.pdf"]) is not None
        assert session.get(LoteConversao, lote_id).situacao == "concluido"
    detalhe = client.get(f"/api/v1/conversoes/{lote_id}", headers=AUTH_OWNER).json()
    assert [d["nome_arquivo"] for d in detalhe["documentos"]] == ["bom.pdf"]


def test_spec_0023_ac_023_apagar_o_ultimo_documento_remove_o_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-006 FR-010 AC-023"""
    from src.app.db import SessionLocal
    from src.app.models import LoteConversao

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido",
        documentos=[{"nome_arquivo": "unico.pdf", "situacao": "concluido"}],
    )

    apagado = client.delete(_url_documento(lote_id, ids["unico.pdf"]), headers=AUTH_OWNER)

    assert apagado.status_code == 204
    with SessionLocal() as session:
        assert session.get(LoteConversao, lote_id) is None
    assert client.get(f"/api/v1/conversoes/{lote_id}", headers=AUTH_OWNER).status_code == 404


def test_spec_0023_ac_024_documento_em_processamento_nao_pode_ser_apagado(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 US-006 FR-010 FR-004 AC-024"""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="processando",
        documentos=[
            {"nome_arquivo": "na-fila.pdf", "situacao": "fila"},
            {"nome_arquivo": "convertendo.pdf", "situacao": "processando"},
        ],
    )

    for nome in ("na-fila.pdf", "convertendo.pdf"):
        resposta = client.delete(_url_documento(lote_id, ids[nome]), headers=AUTH_OWNER)
        assert resposta.status_code == 409
        assert "aguarde" in resposta.json()["detail"].lower()

    with SessionLocal() as session:
        assert session.get(DocumentoConversao, ids["na-fila.pdf"]).situacao == "fila"
        assert session.get(DocumentoConversao, ids["convertendo.pdf"]).situacao == "processando"


def test_spec_0023_ac_025_apagar_exige_escrita_e_respeita_o_escopo(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0023 US-006 FR-008 FR-010 NFR-002 AC-025"""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao

    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    lote_id, ids, _ = _persistir_lote_se_disponivel(
        workspace_id,
        situacao="concluido",
        documentos=[{"nome_arquivo": "sigiloso.pdf", "situacao": "concluido"}],
    )
    url = _url_documento(lote_id, ids["sigiloso.pdf"])

    member = client.delete(url, headers=AUTH_MEMBER)
    externo = client.delete(url, headers=AUTH_OUTRO_TENANT)

    assert member.status_code == 403
    assert "permiss" in member.json()["detail"].lower()
    assert externo.status_code == 404
    with SessionLocal() as session:
        assert session.get(DocumentoConversao, ids["sigiloso.pdf"]) is not None


def test_spec_0033_ac_003_envio_responde_antes_da_conversao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-001 FR-001 FR-002 NFR-001 NFR-003 AC-003"""
    from src.app import tasks as tasks_module
    from tests._pdfs_spec0033 import criar_pdf

    agendados: list[str] = []
    monkeypatch.setattr(
        tasks_module.process_conversion_document_task,
        "defer",
        lambda *, documento_id: agendados.append(documento_id),
    )
    pdf = criar_pdf(tmp_path / "imagens.pdf", ["imagem:Primeira cláusula: ação"] * 3)
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)

    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[("arquivos", ("imagens.pdf", pdf.read_bytes(), "application/pdf"))],
        headers=AUTH_OWNER,
    )

    assert response.status_code == 201
    documento = response.json()["documentos"][0]
    assert documento["situacao"] == "fila"
    assert documento["avisos"] == []
    assert len(agendados) == 1


def test_spec_0033_ac_012_api_devolve_avisos(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-006 FR-007 FR-008 AC-012"""
    from src.app import tasks as tasks_module
    from tests._pdfs_spec0033 import criar_pdf

    agendados: list[str] = []
    monkeypatch.setattr(
        tasks_module.process_conversion_document_task,
        "defer",
        lambda *, documento_id: agendados.append(documento_id),
    )
    com_aviso = criar_pdf(tmp_path / "com-aviso.pdf", ["texto", "imagem:"])
    sem_aviso = criar_pdf(tmp_path / "sem-aviso.pdf", ["texto"])
    client = _cliente_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace(client)
    response = client.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            ("arquivos", ("com-aviso.pdf", com_aviso.read_bytes(), "application/pdf")),
            ("arquivos", ("sem-aviso.pdf", sem_aviso.read_bytes(), "application/pdf")),
        ],
        headers=AUTH_OWNER,
    )
    assert response.status_code == 201
    lote_id = response.json()["id"]
    for documento_id in agendados:
        tasks_module.process_conversion_document_task.func(documento_id=documento_id)

    lote = client.get(f"/api/v1/conversoes/{lote_id}", headers=AUTH_OWNER).json()

    por_nome = {documento["nome_arquivo"]: documento for documento in lote["documentos"]}
    avisos = por_nome["com-aviso.pdf"]["avisos"]
    assert [(a["codigo"], a["pagina"]) for a in avisos] == [("ocr_pouco_texto", 2)]
    assert avisos[0]["mensagem"]
    assert por_nome["sem-aviso.pdf"]["avisos"] == []
