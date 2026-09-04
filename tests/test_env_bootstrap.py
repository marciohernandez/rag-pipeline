"""Testes TDD da SPEC-0009 — isolar a carga do ``.env`` nos entrypoints.

Modelado sobre ``tests/test_provider_boundaries.py`` e
``tests/test_application_boundaries.py``: percorre a AST dos módulos e o
texto-fonte dos entrypoints da raiz.

Fase 1 (prepare): estes casos falham por comportamento ausente —
``src/bootstrap.py`` ainda não existe, ``src/pipeline/config.py`` chama
``load_dotenv()`` no import e nenhum entrypoint da raiz chama ``load_env()``.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT / "src" / "pipeline"

OPERACIONAIS = ("pipeline.py", "search.py", "chat.py", "validate.py", "upsert_from_chunks.py")
ENTRYPOINTS_RAIZ = (
    "pipeline.py",
    "search.py",
    "chat.py",
    "validate.py",
    "upsert_from_chunks.py",
    "main.py",
    "demo_rag.py",
    "inspect_chunks.py",
    "quality.py",
)
DOTENV_NAMES = {"dotenv", "python_dotenv"}


def _module_files(base: Path):
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def dotenv_violations_in_pipeline() -> list[str]:
    """Cada módulo sob src/pipeline/ que importa dotenv ou chama load_dotenv."""
    violacoes: list[str] = []
    for path in _module_files(PIPELINE_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in DOTENV_NAMES:
                        violacoes.append(f"{_relative(path)}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in DOTENV_NAMES:
                    violacoes.append(f"{_relative(path)}: from {node.module}")
            elif isinstance(node, ast.Call):
                func = node.func
                nome = getattr(func, "id", None) or getattr(func, "attr", None)
                if nome == "load_dotenv":
                    violacoes.append(f"{_relative(path)}: chamada load_dotenv")
    return sorted(set(violacoes))


def _has_main_guard(text: str) -> bool:
    return '__name__' in text and '"__main__"' in text or "'__main__'" in text


def entrypoints_sem_load_env() -> list[str]:
    """Arquivos .py da raiz com bloco __main__ que não chamam load_env()."""
    faltando: list[str] = []
    for nome in sorted(p.name for p in ROOT.glob("*.py")):
        texto = (ROOT / nome).read_text(encoding="utf-8")
        if not _has_main_guard(texto):
            continue
        if "load_env(" not in texto:
            faltando.append(nome)
    return faltando


# --- T001 / AC-001 -------------------------------------------------------------

def test_import_de_src_pipeline_nao_injeta_o_env(tmp_path: Path) -> None:
    # SPECSFY: US-001 FR-002 FR-005 NFR-004 AC-001
    marcador = "RAG_ENV_MARCADOR_EXCLUSIVO"
    (tmp_path / ".env").write_text(f"{marcador}=veio-do-dotenv\n", encoding="utf-8")
    codigo = f"import src.pipeline.config, os; print(os.getenv({marcador!r}, ''))"
    ambiente = {k: v for k, v in os.environ.items() if k != marcador}
    ambiente["PYTHONPATH"] = str(ROOT)
    saida = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=tmp_path,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )
    assert saida.stdout.strip() == "", (
        "importar src.pipeline.config injetou o .env do diretório de trabalho no processo"
    )


# --- T002 / AC-002 -----------------------------------------------------------

def test_entrypoints_operacionais_carregam_ambiente_antes_da_config() -> None:
    # SPECSFY: US-002 FR-003 NFR-002 NFR-003 AC-002
    faltando = []
    for nome in OPERACIONAIS:
        texto = (ROOT / nome).read_text(encoding="utf-8")
        if "load_env(" not in texto:
            faltando.append(f"{nome}: sem load_env()")
            continue
        if "load_config(" in texto and texto.index("load_env(") > texto.index("load_config("):
            faltando.append(f"{nome}: load_env() depois de load_config()")
    assert faltando == [], f"entrypoints de operação sem carga explícita de ambiente: {faltando}"


# --- T003 / AC-003 ---------------------------------------------------------

def test_src_pipeline_esta_livre_de_dotenv() -> None:
    # SPECSFY: US-003 FR-002 FR-005 NFR-001 AC-003
    violacoes = dotenv_violations_in_pipeline()
    assert violacoes == [], f"módulos de src/pipeline/ ainda tocam dotenv: {violacoes}"


# --- T004 / AC-004 -------------------------------------------------------

def test_todo_entrypoint_da_raiz_chama_load_env() -> None:
    # SPECSFY: US-003 FR-003 FR-006 AC-004
    faltando = entrypoints_sem_load_env()
    assert faltando == [], f"entrypoints da raiz sem load_env(): {faltando}"


def test_inspect_chunks_esta_no_formato_padrao_de_entrypoint() -> None:
    # SPECSFY: US-003 FR-003 FR-006 AC-004
    texto = (ROOT / "inspect_chunks.py").read_text(encoding="utf-8")
    assert "def main(" in texto, "inspect_chunks.py precisa ter def main()"
    assert _has_main_guard(texto), "inspect_chunks.py precisa do bloco if __name__ == '__main__'"


# --- T005 / AC-005 ---------------------------------------------------------

def test_load_env_e_idempotente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # SPECSFY: US-001 FR-001 FR-004 AC-005
    monkeypatch.chdir(tmp_path)
    from src.bootstrap import load_env

    load_env()
    load_env()


# --- T007 / AC-007 -----------------------------------------------------

def test_carga_do_env_tem_ponto_unico_nos_entrypoints() -> None:
    # SPECSFY: US-003 FR-001 FR-003 FR-007 AC-007
    problemas: list[str] = []
    for nome in ENTRYPOINTS_RAIZ:
        texto = (ROOT / nome).read_text(encoding="utf-8")
        if "from src.bootstrap import load_env" not in texto and "src.bootstrap" not in texto:
            problemas.append(f"{nome}: não importa src.bootstrap.load_env")
        if "load_dotenv" in texto or "from dotenv" in texto or "import dotenv" in texto:
            problemas.append(f"{nome}: ainda referencia dotenv diretamente")
    assert problemas == [], f"a carga do .env não está concentrada no bootstrap: {problemas}"


# --- T008 / AC-008 ---------------------------------------------------

def test_load_env_sem_arquivo_env_nao_levanta_erro(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # SPECSFY: US-002 FR-004 NFR-002 AC-008
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / ".env").exists()
    from src.bootstrap import load_env

    assert load_env() is None


# --- T009 / AC-009 -------------------------------------------------

def test_load_env_nao_sobrescreve_variavel_do_ambiente(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # SPECSFY: US-001 FR-004 NFR-004 AC-009
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "valor-do-ambiente")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=valor-do-dotenv\n", encoding="utf-8")
    from src.bootstrap import load_env

    load_env()
    assert os.environ["OPENAI_API_KEY"] == "valor-do-ambiente"


# --- T011 / AC-011 ---------------------------------------------

def test_scanners_de_fronteira_nomeiam_arquivo_e_import(tmp_path: Path) -> None:
    # SPECSFY: US-003 FR-005 FR-006 NFR-001 AC-011
    # violação sintética no sentido src/pipeline/ -> dotenv
    fake_pkg = tmp_path / "src" / "pipeline"
    fake_pkg.mkdir(parents=True)
    (fake_pkg / "__init__.py").write_text("", encoding="utf-8")
    (fake_pkg / "viola.py").write_text("from dotenv import load_dotenv\n", encoding="utf-8")
    tree_files = list(_module_files(fake_pkg))
    achados = []
    for path in tree_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ImportFrom) and node.module):
                continue
            if node.module.split(".")[0] in DOTENV_NAMES:
                achados.append(f"{path.name}: from {node.module}")
    assert achados == ["viola.py: from dotenv"], achados

    # o scanner real precisa reprovar o estado atual do repositório
    assert dotenv_violations_in_pipeline() == [] and entrypoints_sem_load_env() == [], (
        "a fronteira ainda tem violações reais: "
        f"pipeline={dotenv_violations_in_pipeline()} entrypoints={entrypoints_sem_load_env()}"
    )

    # ocorrência legítima de dotenv fora de src/pipeline/ não é acusada
    legit = tmp_path / "src" / "bootstrap.py"
    legit.write_text("from dotenv import load_dotenv\n", encoding="utf-8")
    assert "bootstrap.py" not in " ".join(dotenv_violations_in_pipeline())


# --- T012 / AC-012 -----------------------------------------

def test_teste_de_credencial_ausente_e_deterministico(tmp_path: Path) -> None:
    # SPECSFY: US-001 FR-002 NFR-004 AC-012
    codigo = textwrap.dedent(
        """
        import os
        import src.pipeline.config  # noqa: F401
        print("KEY" if os.getenv("OPENAI_API_KEY") else "SEM_KEY")
        """
    )
    base_env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    base_env["PYTHONPATH"] = str(ROOT)

    com_dotenv = tmp_path / "com"
    com_dotenv.mkdir()
    (com_dotenv / ".env").write_text("OPENAI_API_KEY=sk-do-dotenv\n", encoding="utf-8")
    sem_dotenv = tmp_path / "sem"
    sem_dotenv.mkdir()

    def _rodar(cwd: Path) -> str:
        return subprocess.run(
            [sys.executable, "-c", codigo],
            cwd=cwd,
            env=base_env,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

    assert _rodar(com_dotenv) == _rodar(sem_dotenv) == "SEM_KEY", (
        "o desfecho de credencial ausente depende do .env do diretório de trabalho"
    )


# --- T013 / AC-013 ---------------------------------

def test_contrato_de_config_yaml_inalterado_para_o_operador() -> None:
    # SPECSFY: US-002 NFR-002 NFR-003 AC-013
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    problemas: list[str] = []
    for nome in OPERACIONAIS:
        texto = (ROOT / nome).read_text(encoding="utf-8")
        # invariante: o comando continua resolvendo config.yaml pela mesma opção
        resultado = subprocess.run(
            [sys.executable, nome, "--help"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode != 0 or "--config" not in resultado.stdout:
            problemas.append(f"{nome}: --help/--config regrediram")
        if "load_config(" not in texto:
            problemas.append(f"{nome}: deixou de resolver config.yaml")
        # mudança: a carga do .env sai do dotenv direto e passa pelo bootstrap
        if "from dotenv" in texto or "import dotenv" in texto:
            problemas.append(f"{nome}: ainda importa dotenv diretamente")
    assert problemas == [], f"contrato do operador não sobreviveu à saída do dotenv: {problemas}"
