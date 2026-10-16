"""Escolha de abas de planilhas (SPEC-0036, US-003, FR-005)."""

from __future__ import annotations

import io

from openpyxl import Workbook

from tests._fase1_conversao import (
    AUTH_OWNER,
    cliente,
    exigir,
    ler_markdown,
    sem_enfileirar,
)

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _planilha_com_tres_abas() -> bytes:
    pasta = Workbook()
    pasta.active.title = "Preços"
    pasta.active.append(["item", "valor"])
    pasta.active.append(["plano básico", "99"])
    for nome, texto in (("Rascunho", "anotação interna"), ("Contatos", "maria@exemplo.com")):
        aba = pasta.create_sheet(nome)
        aba.append(["campo"])
        aba.append([texto])
    saida = io.BytesIO()
    pasta.save(saida)
    return saida.getvalue()


def _enviar(c, workspace_id):
    return c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[("arquivos", ("tabela.xlsx", _planilha_com_tres_abas(), XLSX))],
        headers=AUTH_OWNER,
    )


def _preparar(tmp_path, monkeypatch):
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    enfileirados = sem_enfileirar(monkeypatch)
    return c, _criar_workspace(c), enfileirados


def test_spec_0036_ac_013_planilha_com_varias_abas_aguarda_confirmacao(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0036 US-003 FR-005 NFR-004 NFR-003 AC-013"""
    c, workspace_id, enfileirados = _preparar(tmp_path, monkeypatch)

    resposta = _enviar(c, workspace_id)

    assert resposta.status_code == 201
    documento = resposta.json()["documentos"][0]
    assert documento["situacao"] == "aguardando_abas"
    assert documento["abas"] == ["Preços", "Rascunho", "Contatos"]
    assert enfileirados == []


def test_spec_0036_ac_014_so_as_abas_marcadas_viram_markdown(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-003 FR-005 AC-014"""
    from src.app.storage import get_storage
    from tests._fase1_conversao import executar

    c, workspace_id, enfileirados = _preparar(tmp_path, monkeypatch)
    lote = _enviar(c, workspace_id).json()
    documento = lote["documentos"][0]

    confirmacao = c.post(
        f"/api/v1/conversoes/{lote['id']}/documentos/{documento['id']}/abas",
        json={"abas": ["Preços", "Contatos"]},
        headers=AUTH_OWNER,
    )

    assert confirmacao.status_code == 200
    assert confirmacao.json()["situacao"] == "fila"
    assert enfileirados == [documento["id"]]
    executar(documento["id"])
    md = ler_markdown(get_storage(), documento["id"], "tabela.md", tmp_path)
    assert "## Preços" in md and "## Contatos" in md
    assert "Rascunho" not in md and "anotação interna" not in md


def test_spec_0036_xlsx_converter_aceita_lista_de_abas(tmp_path) -> None:
    """SPECSFY: SPEC-0036 US-003 FR-005 AC-014 contrato do conversor"""
    modulo = exigir("src.pipeline.conversion.converters.xlsx")
    arquivo = tmp_path / "tabela.xlsx"
    arquivo.write_bytes(_planilha_com_tres_abas())

    resultado = modulo.XlsxConverter(abas=["Contatos"]).converter(arquivo)

    assert "## Contatos" in resultado.markdown
    assert "## Preços" not in resultado.markdown


def test_spec_0036_ac_015_sem_nenhuma_aba_marcada_a_api_recusa(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-003 FR-005 NFR-004 AC-015 contrato da API"""
    c, workspace_id, enfileirados = _preparar(tmp_path, monkeypatch)
    lote = _enviar(c, workspace_id).json()
    documento = lote["documentos"][0]
    url = f"/api/v1/conversoes/{lote['id']}/documentos/{documento['id']}/abas"

    vazio = c.post(url, json={"abas": []}, headers=AUTH_OWNER)
    inexistente = c.post(url, json={"abas": ["Não existe"]}, headers=AUTH_OWNER)

    assert vazio.status_code == 400 and inexistente.status_code == 400
    assert enfileirados == []
    atual = c.get(f"/api/v1/conversoes/{lote['id']}", headers=AUTH_OWNER).json()
    assert atual["documentos"][0]["situacao"] == "aguardando_abas"
