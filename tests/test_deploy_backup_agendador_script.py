"""Agendador diário do ciclo de backup (SPEC-0034).

Fase RED: `deploy/backup/agendar.sh` ainda não existe.
"""

from __future__ import annotations

import stat
from pathlib import Path

from tests._backup_falso import AmbienteBackup


def test_agendador_calcula_a_proxima_janela_e_sobrevive_a_falhas(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 FR-001 NFR-003 NFR-004 AC-018"""
    amb = AmbienteBackup(tmp_path)

    # A espera vai até a próxima 03:00; na própria 03:00 a próxima janela é a de amanhã.
    esperas = {"02:00:00": "3600", "03:00:00": "86400", "04:30:00": "81000"}
    for agora, esperado in esperas.items():
        resultado = amb.agendar("--espera", agora, BACKUP_HORA="03:00")
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip() == esperado, (agora, resultado.stdout)

    # Uma falha do ciclo não derruba o agendador: ele segue para a janela seguinte.
    ciclo = tmp_path / "ciclo_falho.sh"
    ciclo.write_text(f'#!/usr/bin/env bash\necho x >> "{tmp_path}/ciclos.log"\nexit 1\n')
    ciclo.chmod(ciclo.stat().st_mode | stat.S_IEXEC)
    laco = amb.agendar(
        "--iteracoes",
        "2",
        BACKUP_HORA="03:00",
        BACKUP_CICLO=str(ciclo),
        BACKUP_SEM_ESPERA="1",
    )
    assert laco.returncode == 0, laco.stderr
    assert len((tmp_path / "ciclos.log").read_text().splitlines()) == 2
    assert "falh" in (laco.stdout + laco.stderr).lower()
