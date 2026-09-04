"""Fronteira estática da SPEC-0004 — validação somente leitura.

Arquivo próprio, separado de ``tests/test_provider_boundaries.py``: aquele
carrega marcadores da SPEC-0003 cujos IDs coincidem com os desta fatia, o que
faria o auditor contar cobertura alheia como se fosse desta spec.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTOTIPOS = (
    ROOT / "scripts" / "check_qdrant_connection.py",
    ROOT / "scripts" / "check_qdrant_search.py",
)
MODULOS_DE_VALIDACAO = (
    ROOT / "src" / "pipeline" / "validation.py",
    ROOT / "validate.py",
)
SDKS_PROIBIDOS = {
    "qdrant_client",
    "chromadb",
    "pinecone",
    "langchain_qdrant",
    "langchain_chroma",
    "langchain_pinecone",
    "langchain_huggingface",
    "langchain_openai",
}
# Identificadores de cliente que não podem voltar ao código de validação.
IDENTIFICADORES_DE_CLIENTE = ("vivo_gold_banda_larga_pf", "Vivo Fibra", "Vivo_Gold")


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_ac_014_prototipos_removidos_e_sem_identificador_de_cliente() -> None:
    # SPECSFY: US-001 FR-001 FR-007 NFR-002 AC-014
    existentes = [str(path.relative_to(ROOT)) for path in PROTOTIPOS if path.exists()]
    assert existentes == []

    vazamentos = [
        f"{path.relative_to(ROOT)}: {marca}"
        for path in MODULOS_DE_VALIDACAO
        if path.exists()
        for marca in IDENTIFICADORES_DE_CLIENTE
        if marca in path.read_text(encoding="utf-8")
    ]
    assert vazamentos == []


def test_ac_016_validacao_acessa_o_destino_apenas_pelos_contratos() -> None:
    # SPECSFY: FR-007 NFR-002 AC-016
    ausentes = [
        str(path.relative_to(ROOT))
        for path in MODULOS_DE_VALIDACAO
        if not path.exists()
    ]
    assert ausentes == []

    violacoes = sorted(
        f"{path.relative_to(ROOT)}: {modulo}"
        for path in MODULOS_DE_VALIDACAO
        for modulo in _imports(path)
        if modulo.split(".")[0] in SDKS_PROIBIDOS
    )
    assert violacoes == []
