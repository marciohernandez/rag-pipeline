"""Runbook do deploy em Compose (SPEC-0045).

Fase RED: `deploy/RUNBOOK_COMPOSE.md` e o `deploy.sh` ainda não existem.
"""

from __future__ import annotations

import re

from tests._compose_deploy import DEPLOY_SH, RUNBOOK, texto_de


def test_primeira_instalacao_na_ordem_e_sem_segredos() -> None:
    """SPECSFY: SPEC-0045 US-002 FR-008 NFR-003 AC-014"""
    texto = texto_de(RUNBOOK)
    assert "## Primeira instalação" in texto
    ordem = ("chmod 600", "known_hosts", "deploy key", "DNS", "DEPLOY_CONFIG")
    posicoes = [texto.find(item) for item in ordem]
    assert all(p >= 0 for p in posicoes), dict(zip(ordem, posicoes, strict=True))
    assert "docker compose -p ragpipeline" in texto
    assert not re.search(r"sk-[A-Za-z0-9]{10,}|BEGIN [A-Z ]*PRIVATE KEY", texto)


def test_verificacao_pos_deploy_prova_dns_e_https() -> None:
    """SPECSFY: SPEC-0045 US-002 FR-008 NFR-003 AC-015"""
    texto = texto_de(RUNBOOK)
    verificacao = texto[texto.index("## Verificação") :]
    for item in ("curl -I https://", "certificado", "healthy", "logs"):
        assert item in verificacao, item
    assert "container saudável" in verificacao.lower() and "não prova" in verificacao.lower()


def test_retorno_a_versao_anterior_sem_construir_nem_apagar() -> None:
    """SPECSFY: SPEC-0045 US-002 FR-008 NFR-003 AC-016"""
    texto = texto_de(RUNBOOK)
    retorno = texto[texto.index("## Retorno") :]
    assert "--versao" in retorno and "sem construir" in retorno
    assert "down -v" not in retorno.replace("nunca `down -v`", "")
    assert "--versao" in texto_de(DEPLOY_SH)
