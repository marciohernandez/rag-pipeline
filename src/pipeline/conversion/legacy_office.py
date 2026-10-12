"""Normalização de formatos Office legados via LibreOffice headless (SPEC-0023, DEC-006)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from src.pipeline.conversion.contracts import ConversionError

_MAPEAMENTO_LEGADO = {"doc": "docx", "ppt": "pptx", "xls": "xlsx"}
_TIMEOUT_SEGUNDOS = 60


def normalizar_formato_legado(caminho: Path, extensao: str) -> Path:
    """Converte `.doc`/`.ppt`/`.xls` para o equivalente OOXML antes da extração."""
    extensao_destino = _MAPEAMENTO_LEGADO.get(extensao.strip().lower().lstrip("."))
    if extensao_destino is None:
        raise ConversionError(f"Formato legado não suportado: {extensao!r}")

    pasta_saida = Path(tempfile.mkdtemp(prefix="specsfy-legacy-"))
    comando = [
        "soffice",
        "--headless",
        "--convert-to",
        extensao_destino,
        "--outdir",
        str(pasta_saida),
        str(caminho),
    ]
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SEGUNDOS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise ConversionError(
            f"Falha ao normalizar formato legado: {caminho.name}"
        ) from erro

    if resultado.returncode != 0:
        raise ConversionError(
            f"LibreOffice falhou ao normalizar {caminho.name}: {resultado.stderr}"
        )

    return pasta_saida / f"{caminho.stem}.{extensao_destino}"
