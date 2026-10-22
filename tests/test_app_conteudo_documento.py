"""Conteúdo processado guardado pelo worker (SPEC-0031, AC-007 e AC-009).

Fase RED: ``ConteudoDocumento`` e a gravação em ``_registrar_documento`` não existem.
"""

from __future__ import annotations

import dataclasses
import json

from tests._colecoes import (
    criar_colecao,
    documentos,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)
from tests._copilot import conteudos_do_banco


def _etiqueta_produto() -> str:
    return json.dumps([{"rotulo": "categoria", "valor": "produto"}])


def test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007"""
    ambiente = preparar(tmp_path, monkeypatch)
    texto = texto_com_secoes(3)
    resposta = enviar(
        ambiente, [md("manual.md", texto)], nova="manuais", metadados_chunk=_etiqueta_produto()
    )
    assert resposta.status_code == 201, resposta.text
    colecao_id = resposta.json()["colecao_id"]
    documento = documentos(ambiente, colecao_id)[0]

    guardados = conteudos_do_banco(colecao_id)

    assert len(guardados) == 1
    conteudo = guardados[0]
    assert conteudo.documento_id == documento["id"]
    assert conteudo.envio_id == resposta.json()["envio_id"]
    assert conteudo.texto == texto and conteudo.truncado is False
    assert len(conteudo.trechos) == documento["chunks"] >= 2
    assert [t["ordem"] for t in conteudo.trechos] == list(range(1, documento["chunks"] + 1))
    assert all(t["texto"].strip() for t in conteudo.trechos)
    assert all(t["etiquetas"] == {"categoria": "produto"} for t in conteudo.trechos)

    ambiente.armazem.falhar_escrita = True
    falha = enviar(ambiente, [md("falha.md", texto_com_secoes(2, "f"))], nova="com-falha")
    assert falha.status_code == 201, falha.text
    envio = ambiente.client.get(
        f"/api/v1/envios/{falha.json()['envio_id']}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    ).json()
    assert envio["situacao"] == "failed"
    assert conteudos_do_banco(falha.json()["colecao_id"]) == []


def test_texto_acima_do_limite_e_guardado_truncado_com_marcador(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007"""
    from src.app import settings

    ambiente = preparar(tmp_path, monkeypatch)
    atual = settings.get_settings()
    if not hasattr(atual, "conteudo_max_caracteres"):
        raise AssertionError("AppSettings.conteudo_max_caracteres ainda não existe (SPEC-0031)")
    monkeypatch.setattr(
        settings, "_SETTINGS", dataclasses.replace(atual, conteudo_max_caracteres=50)
    )
    texto = texto_com_secoes(4)
    assert len(texto) > 50

    resposta = enviar(ambiente, [md("longo.md", texto)], nova="longos")

    assert resposta.status_code == 201, resposta.text
    colecao_id = resposta.json()["colecao_id"]
    envio = ambiente.client.get(
        f"/api/v1/envios/{resposta.json()['envio_id']}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    ).json()
    assert envio["situacao"] == "succeeded"
    conteudo = conteudos_do_banco(colecao_id)[0]
    assert conteudo.truncado is True
    assert conteudo.texto == texto[:50]
    assert sum(len(t["texto"]) for t in conteudo.trechos) > 50
    assert len(conteudo.trechos) == documentos(ambiente, colecao_id)[0]["chunks"]


def test_nova_versao_substitui_e_reenvio_identico_nao_altera(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-009"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais", [md("a.md", texto_com_secoes(3, "v1"))])
    versao_1 = conteudos_do_banco(colecao_id)
    assert len(versao_1) == 1 and "v1" in versao_1[0].texto

    nova = enviar(ambiente, [md("a.md", texto_com_secoes(3, "v2"))], colecao_id=colecao_id)
    assert nova.status_code == 201, nova.text
    versao_2 = conteudos_do_banco(colecao_id)

    assert len(versao_2) == 1
    assert "v2" in versao_2[0].texto and "v1" not in versao_2[0].texto
    assert all("v2" in t["texto"] for t in versao_2[0].trechos)
    assert versao_2[0].envio_id == nova.json()["envio_id"]
    assert versao_2[0].documento_id == versao_1[0].documento_id

    identico = enviar(ambiente, [md("a.md", texto_com_secoes(3, "v2"))], colecao_id=colecao_id)
    assert identico.status_code == 201, identico.text
    depois = conteudos_do_banco(colecao_id)
    assert len(depois) == 1
    assert depois[0].atualizado_em == versao_2[0].atualizado_em
    assert depois[0].envio_id == versao_2[0].envio_id
