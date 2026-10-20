"""Backup contra o Postgres externo (SPEC-0041).

Fase RED: o ciclo usa host interno fixo e não repassa `PGSSLMODE`. Os casos usam os
binários falsos de `tests/_backup_falso.py`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from tests._backup_falso import AmbienteBackup

EXTERNO = {
    "PGHOST": "db.exemplo.invalid",
    "PGPORT": "5432",
    "PGUSER": "usuario.ref",
    "PGDATABASE": "postgres",
    "PGSSLMODE": "require",
}
QUARTA = "2026-10-14"
STACK = Path(__file__).resolve().parent.parent / "deploy" / "stack.prod.yml"


def _variaveis_vistas_pelo_dump(amb: AmbienteBackup) -> str:
    return "\n".join(amb.log("pg_dump_env"))


def test_backup_usa_as_variaveis_do_postgres_externo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0041 US-003 FR-004 NFR-001 AC-008"""
    amb = AmbienteBackup(tmp_path)
    amb.trocar_pg_dump_para_registrar_ambiente()

    resultado = amb.backup(BACKUP_DATA=QUARTA, **EXTERNO)

    assert resultado.returncode == 0, resultado.stderr
    vistas = _variaveis_vistas_pelo_dump(amb)
    for chave, valor in EXTERNO.items():
        assert f"{chave}={valor}" in vistas
    assert amb.objetos() == [f"diarios/{QUARTA}.dump.enc"]
    assert "PGPASSWORD=" not in resultado.stdout + resultado.stderr
    ambiente = yaml.safe_load(STACK.read_text())["services"]["backup_ragpipeline"]["environment"]
    for chave in ("PGHOST", "PGPORT", "PGUSER", "PGDATABASE", "PGSSLMODE"):
        assert "DATABASE_" in str(ambiente.get(chave)), f"{chave} não vem das variáveis DATABASE_*"


def test_postgres_externo_inacessivel_preserva_o_backup_anterior(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0041 US-003 FR-004 NFR-002 AC-009"""
    amb = AmbienteBackup(tmp_path)
    amb.trocar_pg_dump_para_registrar_ambiente()
    amb.semear("diarios/2026-10-13.dump.enc")

    resultado = amb.backup(BACKUP_DATA=QUARTA, FAKE_PG_DUMP_FALHA="1", **EXTERNO)

    assert resultado.returncode != 0
    assert "resultado=falha" in resultado.stdout
    assert "diarios/2026-10-13.dump.enc" in amb.objetos()
    assert f"diarios/{QUARTA}.dump.enc" not in amb.objetos()
    assert "PGHOST=db.exemplo.invalid" in _variaveis_vistas_pelo_dump(amb)

    sem_host = amb.backup(BACKUP_DATA=QUARTA, PGHOST="")
    assert sem_host.returncode != 0, "sem PGHOST o backup não pode assumir o host interno"
    assert "postgres_ragpipeline" not in "\n".join(amb.log("pg_dump_env"))
