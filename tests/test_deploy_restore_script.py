"""Restauração de um backup em banco temporário (SPEC-0034).

Fase RED: `deploy/backup/restaurar.sh` ainda não existe. Os casos usam `psql`,
`pg_restore` e `aws` falsos; o `openssl` é o real.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests._backup_falso import CHAVE, DUMP_EM_CLARO, AmbienteBackup

OBJETO = "diarios/2026-10-14.dump.enc"
DESTINO = "banco-destino.invalid:5432"


def _preparar(amb: AmbienteBackup) -> list[str]:
    """Gera um backup real pelo ciclo e devolve os argumentos base da restauração."""
    assert amb.backup(BACKUP_DATA="2026-10-14").returncode == 0
    return [
        OBJETO,
        "--destino",
        DESTINO,
        "--chave-arquivo",
        str(amb.segredos / "backup_chave"),
        "--credenciais-arquivo",
        str(amb.segredos / "backup_r2_credentials"),
    ]


def test_restaura_num_banco_temporario_novo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-003 FR-007 NFR-001 AC-011"""
    amb = AmbienteBackup(tmp_path)
    argumentos = _preparar(amb)
    for chamada in ("psql", "pg_restore"):
        (amb.logs / f"{chamada}.log").unlink(missing_ok=True)

    resultado = amb.restaurar(*argumentos)

    assert resultado.returncode == 0, resultado.stderr
    criados = [
        linha for linha in amb.bancos.read_text().splitlines() if linha.startswith("restauracao_")
    ]
    assert len(criados) == 1 and re.fullmatch(r"restauracao_\d{14}", criados[0]), criados
    assert criados[0] in resultado.stdout
    restauracoes = [c for c in amb.log("pg_restore") if criados[0] in c]
    assert restauracoes, "pg_restore deve apontar para o banco novo"
    assert CHAVE not in amb.tudo_que_vaza(resultado)


def test_recusa_objeto_inexistente_ou_chave_errada_sem_criar_banco(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-012"""
    amb = AmbienteBackup(tmp_path)
    argumentos = _preparar(amb)
    bancos_antes = amb.bancos.read_text()

    inexistente = amb.restaurar("diarios/2020-01-01.dump.enc", *argumentos[1:])
    assert inexistente.returncode != 0
    assert (inexistente.stdout + inexistente.stderr).strip()

    chave_errada = tmp_path / "chave_errada"
    chave_errada.write_text("outra-chave-qualquer")
    errada = amb.restaurar(
        OBJETO, "--destino", DESTINO, "--chave-arquivo", str(chave_errada),
        "--credenciais-arquivo", str(amb.segredos / "backup_r2_credentials"),
    )  # fmt: skip
    assert errada.returncode != 0

    assert amb.bancos.read_text() == bancos_antes, "nenhum banco pode ser criado"
    assert not any("CREATE DATABASE" in c for c in amb.log("psql"))
    assert list(amb.tmp.iterdir()) == []


def test_nunca_restaura_sobre_banco_existente_nem_apaga_objetos(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-013"""
    amb = AmbienteBackup(tmp_path)
    argumentos = _preparar(amb)
    bancos_antes = amb.bancos.read_text()

    recusa = amb.restaurar(*argumentos, "--banco", "rag_pipeline")

    assert recusa.returncode != 0
    assert amb.bancos.read_text() == bancos_antes
    assert not any("restauracao_" in c or "rag_pipeline" in c for c in amb.log("pg_restore"))

    sucesso = amb.restaurar(*argumentos)
    assert sucesso.returncode == 0, sucesso.stderr
    comandos = "\n".join(amb.log("psql") + amb.log("pg_restore")).lower()
    for proibido in ("--clean", "drop ", "truncate"):
        assert proibido not in comandos, proibido
    assert {"postgres", "rag_pipeline"} <= set(amb.bancos.read_text().split())
    assert DUMP_EM_CLARO not in sucesso.stdout
