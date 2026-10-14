"""Testes do script `deploy/conferir_dominio.sh` (SPEC-0032).

Rodam contra `curl`, `openssl` e `getent` falsos (`tests/_rede_falsa.py`); nenhum
teste consulta rede, DNS real, Traefik ou banco.
"""

import re
from pathlib import Path

from tests._rede_falsa import DOMINIO_DE_TESTE, VERIFICACOES, RedeFalsa

LIMITE_POR_CONSULTA = re.compile(r"(--max-time|-m)[ =]10\b")


def test_conferencia_aprova_dominio_correto(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-004 FR-005 NFR-003 AC-010"""
    rede = RedeFalsa(tmp_path)

    execucao = rede.rodar(DOMINIO_DE_TESTE)

    assert execucao.codigo == 0, execucao.saida
    for nome in VERIFICACOES:
        assert re.search(rf"^OK\b.*{nome}", execucao.saida, re.MULTILINE), (
            f"verificação {nome} não aparece como aprovada:\n{execucao.saida}"
        )
    assert "FALHA" not in execucao.saida


def test_conferencia_nomeia_cada_falha_e_sai_com_erro(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-004 FR-005 NFR-003 FR-003 AC-011"""
    cenarios = {
        "DNS": {"FAKE_SEM_DNS": "1"},
        "Certificado": {"FAKE_CERT_INVALIDO": "1"},
        "Redirecionamento": {"FAKE_SEM_REDIRECT": "1"},
        "HSTS": {"FAKE_SEM_HSTS": "1"},
    }
    for nome, falha in cenarios.items():
        rede = RedeFalsa(tmp_path / nome)

        execucao = rede.rodar(DOMINIO_DE_TESTE, **falha)

        assert execucao.codigo != 0, f"{nome}: o script deveria falhar"
        assert re.search(rf"^FALHA\b.*{nome}", execucao.saida, re.MULTILINE), (
            f"{nome}: a verificação reprovada não foi nomeada:\n{execucao.saida}"
        )
        if nome != "DNS":
            assert re.search(r"^OK\b.*DNS", execucao.saida, re.MULTILINE), (
                f"{nome}: o script parou antes de listar as demais verificações"
            )


def test_conferencia_sem_dominio_recusa_sem_consultar_rede(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-004 FR-005 NFR-001 AC-012"""
    rede = RedeFalsa(tmp_path)

    execucao = rede.rodar()

    assert execucao.codigo != 0
    assert "uso" in execucao.saida.lower()
    assert "DOMINIO_RAGPIPELINE" in execucao.saida
    assert rede.chamadas() == []


def test_conferencia_tem_tempo_limite_e_termina_em_60s(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-004 NFR-003 AC-016"""
    rede = RedeFalsa(tmp_path)

    execucao = rede.rodar(DOMINIO_DE_TESTE, FAKE_LENTO="15")

    assert execucao.codigo != 0
    assert execucao.duracao < 60, f"o script levou {execucao.duracao:.0f}s"
    consultas = [c for c in rede.chamadas() if c.startswith("curl ")]
    assert consultas, "o script não consultou o domínio"
    for consulta in consultas:
        assert LIMITE_POR_CONSULTA.search(consulta), (
            f"consulta sem tempo limite de 10 segundos: {consulta}"
        )
