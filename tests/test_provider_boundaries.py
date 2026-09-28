"""Teste estático de fronteira — AC-003.

Corte limpo: ``src/pipeline/embedder.py`` e seus imports não existem; SDKs de vector
store e classes de embeddings aparecem somente em ``src/pipeline/providers/``;
``ChatOpenAI`` em ``chat.py`` permanece a única exceção temporária rastreada
pelo BACKLOG-0010.

A varredura é feita sobre a AST de cada módulo Python do repositório, fora de
``tests/`` e de ``src/pipeline/providers/``.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_DIR = ROOT / "src" / "pipeline" / "providers"
EMBEDDER_MODULE = "src.pipeline.embedder"

# SDKs de vector store e classes de embeddings que só podem viver em src/pipeline/providers/.
FORBIDDEN_MODULES = {
    "qdrant_client",
    "chromadb",
    "pinecone",
    "langchain_qdrant",
    "langchain_chroma",
    "langchain_pinecone",
    "langchain_huggingface",
}
FORBIDDEN_SYMBOLS = {
    "OpenAIEmbeddings",
    "HuggingFaceEmbeddings",
    "Chroma",
    "Qdrant",
    "QdrantVectorStore",
    "PineconeVectorStore",
}
# Exceção temporária: a cadeia de chat ainda usa o LLM diretamente (BACKLOG-0010).
ALLOWED_EXCEPTIONS = {("chat.py", "ChatOpenAI")}

_SKIP_DIRS = {".venv", "venv", "build", "dist", "__pycache__", "tests"}


def _iter_module_files():
    for path in ROOT.rglob("*.py"):
        if set(path.relative_to(ROOT).parts) & _SKIP_DIRS:
            continue
        if PROVIDERS_DIR in path.parents:
            continue
        yield path


def _imports(path: Path):
    """Devolve `(módulo, símbolo)` de cada import do arquivo."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, alias.name.split(".")[-1]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                yield module, alias.name


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_embedder_monolitico_foi_removido() -> None:
    # SPECSFY: US-001 FR-001 FR-003 FR-007 NFR-003 NFR-004 AC-003
    assert not (ROOT / "src" / "pipeline" / "embedder.py").exists()


def test_nenhum_consumidor_importa_embedder() -> None:
    # SPECSFY: US-001 FR-001 FR-003 FR-007 NFR-003 NFR-004 AC-003
    ofensores = sorted(
        {
            _relative(path)
            for path in _iter_module_files()
            for module, _symbol in _imports(path)
            if module == EMBEDDER_MODULE or module.startswith(f"{EMBEDDER_MODULE}.")
        }
    )
    assert ofensores == []


def test_sdks_de_provider_confinados_a_src_providers() -> None:
    # SPECSFY: US-001 FR-001 FR-003 FR-007 NFR-003 NFR-004 AC-003
    violacoes = sorted(
        {
            f"{_relative(path)}: {module or symbol}"
            for path in _iter_module_files()
            for module, symbol in _imports(path)
            if module.split(".")[0] in FORBIDDEN_MODULES
            or (
                symbol in FORBIDDEN_SYMBOLS
                and (_relative(path), symbol) not in ALLOWED_EXCEPTIONS
            )
        }
    )
    assert violacoes == []


def test_chatopenai_em_chat_py_e_a_unica_excecao() -> None:
    # SPECSFY: US-001 FR-001 FR-003 FR-007 NFR-003 NFR-004 AC-003
    excecoes_reais = {
        (_relative(path), symbol)
        for path in _iter_module_files()
        for _module, symbol in _imports(path)
        if symbol == "ChatOpenAI"
    }
    assert excecoes_reais == ALLOWED_EXCEPTIONS


def test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada() -> None:
    # SPECSFY: SPEC-0021 FR-012 AC-024
    ofensores = sorted(
        {
            f"{_relative(path)}: {module}"
            for path in _iter_module_files()
            for module, _symbol in _imports(path)
            if module.split(".")[0] == "langchain_openai"
            and _relative(path) != "chat.py"
        }
    )
    assert ofensores == []

    # src/app depende somente da fachada do pipeline; a fachada precisa expor o assistente
    for path in (ROOT / "src" / "app").rglob("*.py"):
        for module, _symbol in _imports(path):
            if module.startswith("src.pipeline"):
                assert module.split(".")[:3] == ["src", "pipeline", "service"], (
                    f"{_relative(path)} importa {module}, não a fachada"
                )
    service = (ROOT / "src" / "pipeline" / "service.py").read_text(encoding="utf-8")
    assert "def assistant_reply" in service and "def index_assistant_knowledge" in service
    assert (PROVIDERS_DIR / "llm" / "openrouter.py").exists()
