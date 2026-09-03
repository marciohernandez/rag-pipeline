"""Teste estático de fronteira da SPEC-0008 — ``src/app/`` ↔ ``src/pipeline/``.

Modelado sobre ``tests/test_provider_boundaries.py``: percorre a AST de cada
módulo Python e reprova a violação da fronteira nos dois sentidos.

- de ``src/app/`` só é permitido importar a fachada ``src.pipeline.service``;
  qualquer outro alvo dentro de ``src.pipeline`` reprova, nomeando arquivo e
  módulo;
- de ``src/pipeline/`` nenhum import de ``src.app`` é permitido, porque
  inverteria a dependência entre as camadas.

O caso de ``src/app/`` vazio precisa passar sem falso positivo.

Enquanto ``src/app/`` e ``src/pipeline/`` não existirem (T014), os casos falham
por estrutura ausente — esse é o RED esperado da fase 1.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "src" / "app"
PIPELINE_DIR = ROOT / "src" / "pipeline"

FACHADA_MODULE = "src.pipeline.service"
PIPELINE_PREFIX = "src.pipeline"
APP_PREFIX = "src.app"


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _module_files(base: Path):
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def test_estrutura_da_fronteira_existe() -> None:
    # SPECSFY: US-003 FR-002 FR-006 NFR-001 AC-005
    assert APP_DIR.is_dir(), "src/app/ ainda não existe"
    assert PIPELINE_DIR.is_dir(), "src/pipeline/ ainda não existe"


def test_src_app_so_importa_a_fachada_de_src_pipeline() -> None:
    # SPECSFY: US-003 FR-002 FR-006 NFR-001 AC-005
    assert APP_DIR.is_dir(), "src/app/ ainda não existe"
    violacoes = sorted(
        f"{_relative(path)}: {module}"
        for path in _module_files(APP_DIR)
        for module in _imports(path)
        if (module == PIPELINE_PREFIX or module.startswith(f"{PIPELINE_PREFIX}."))
        and module != FACHADA_MODULE
    )
    assert violacoes == [], f"imports internos proibidos a partir de src/app/: {violacoes}"


def test_src_pipeline_nao_importa_a_camada_de_aplicacao() -> None:
    # SPECSFY: US-003 FR-002 FR-006 NFR-001 AC-005
    assert PIPELINE_DIR.is_dir(), "src/pipeline/ ainda não existe"
    violacoes = sorted(
        f"{_relative(path)}: {module}"
        for path in _module_files(PIPELINE_DIR)
        for module in _imports(path)
        if module == APP_PREFIX or module.startswith(f"{APP_PREFIX}.")
    )
    assert violacoes == [], f"inversão de dependência src/pipeline/ -> src.app: {violacoes}"


def test_import_autorizado_da_fachada_e_aceito() -> None:
    # SPECSFY: US-003 FR-003 FR-006 AC-006
    assert APP_DIR.is_dir(), "src/app/ ainda não existe"
    autorizados = {
        module
        for path in _module_files(APP_DIR)
        for module in _imports(path)
        if module.startswith(PIPELINE_PREFIX)
    }
    assert autorizados <= {FACHADA_MODULE}, (
        f"src/app/ só pode importar {FACHADA_MODULE}; encontrou {sorted(autorizados)}"
    )


def test_pacote_app_vazio_nao_produz_falso_positivo() -> None:
    # SPECSFY: US-003 FR-003 FR-006 AC-006
    assert APP_DIR.is_dir(), "src/app/ ainda não existe"
    modulos = [p for p in _module_files(APP_DIR) if p.name != "__init__.py"]
    if not modulos:
        # pacote vazio: a varredura não tem o que inspecionar e deve passar
        assert list(_module_files(APP_DIR)) == [] or all(
            p.name == "__init__.py" for p in _module_files(APP_DIR)
        )
