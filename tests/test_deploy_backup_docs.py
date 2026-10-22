"""Documento de operação do backup (SPEC-0034).

Fase RED: `deploy/BACKUP.md` ainda não existe.
"""

from __future__ import annotations

import re
from pathlib import Path

DOCUMENTO = Path(__file__).resolve().parent.parent / "deploy" / "BACKUP.md"


def _texto() -> str:
    assert DOCUMENTO.exists(), "deploy/BACKUP.md ainda não existe"
    return DOCUMENTO.read_text(encoding="utf-8")


def test_documenta_onde_a_chave_fica_guardada() -> None:
    """SPECSFY: SPEC-0034 US-003 FR-010 NFR-001 AC-019"""
    texto = _texto().lower()

    assert "fora da vps" in texto
    assert "gerenciador de senhas" in texto
    assert "sem a chave" in texto and "não pode ser restaurado" in texto
    assert not re.search(r"(AKIA[0-9A-Z]{8,}|-----BEGIN|password\s*=\s*\S+)", _texto())


def test_documenta_a_restauracao_e_a_conferencia() -> None:
    """SPECSFY: SPEC-0034 US-003 FR-007 FR-010 AC-021"""
    texto = _texto().lower()

    assert "restaurar.sh" in texto
    assert "banco temporário" in texto
    assert "conferir" in texto or "conferência" in texto
    assert "desenvolvimento" in texto and "nunca" in texto


def test_documenta_avisos_falhas_e_operacao() -> None:
    """SPECSFY: SPEC-0034 US-002 FR-006 FR-010 AC-022"""
    texto = _texto().lower()

    assert "7 diários" in texto and "4 semanais" in texto
    assert "03:00" in texto
    assert "ciclo manual" in texto
    assert "verificação real" in texto and "r2" in texto
    for etapa in ("dump", "cifrar", "enviar", "verificar", "reter"):
        assert etapa in texto, etapa
