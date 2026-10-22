"""Fatia SPEC-0010 — Enxugar providers concretos para Qdrant.

O projeto mantém a abstração multi-provider (contrato neutro, backend port,
``ProviderFactory``, ``InMemoryVectorStoreAdapter``), mas deixa de carregar as
implementações concretas ainda não escolhidas — ChromaDB e Pinecone — e suas
dependências. Estes casos derivam do BDD da seção 6 da spec e cada um traz o
seu próprio marcador ``SPECSFY:``.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_REMOVED_SYMBOLS = (
    "_ChromaBackend",
    "_PineconeBackend",
    "ChromaVectorStoreAdapter",
    "PineconeVectorStoreAdapter",
)
_REMOVED_DEPS = ("chromadb", "langchain-chroma", "langchain-pinecone")
_CONTRACTS = ROOT / "src" / "pipeline" / "providers" / "contracts.py"
# Snapshot do contrato neutro no início da SPEC-0010; a fatia não pode alterá-lo.
# SPEC-0021 acrescentou ChatMessage e ChatModelAdapter a contracts.py; o restante é intacto.
# SPEC-0030 acrescentou `LogicalScope.document_id`; o hash acompanha essa única mudança.
# SPEC-0036/DEC-007: ChatImage e imagens opcionais em ChatMessage.
# Comparação AST comprovou os demais contratos preservados.
_CONTRACTS_SHA256 = "e717157fdd7556d7e1073511d24f519f7808636d906c0496deaba108e8936c75"


def _iter_source_files():
    for base in ("src", "tests"):
        for path in (ROOT / base).rglob("*.py"):
            if "chunk.egg-info" in path.parts:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            yield path


def test_vector_store_registry_has_only_maintained_providers() -> None:
    # SPECSFY: US-001 FR-001 FR-004 NFR-002 AC-001
    from src.pipeline.providers import factory

    assert set(factory._VECTOR_STORES) == {"qdrant", "in_memory"}
    source = _CONTRACTS.parent.joinpath("factory.py").read_text(encoding="utf-8").lower()
    assert "chroma" not in source
    assert "pinecone" not in source


def test_create_vector_store_chroma_raises_unknown_provider() -> None:
    # SPECSFY: US-002 FR-001 FR-002 FR-004 AC-002
    from src.pipeline.providers import UnknownProviderError
    from src.pipeline.providers.factory import ProviderFactory

    with pytest.raises(UnknownProviderError) as excinfo:
        ProviderFactory.create_vector_store("chroma", {})
    message = str(excinfo.value)
    assert "in_memory" in message and "qdrant" in message


def test_create_vector_store_pinecone_raises_unknown_provider() -> None:
    # SPECSFY: US-001 FR-001 FR-002 NFR-002 AC-003
    from src.pipeline.providers import UnknownProviderError
    from src.pipeline.providers.factory import ProviderFactory

    with pytest.raises(UnknownProviderError) as excinfo:
        ProviderFactory.create_vector_store("pinecone", {})
    options = str(excinfo.value).split("Opções:")[-1]
    assert "pinecone" not in options


def test_pyproject_has_no_chroma_or_pinecone_deps() -> None:
    # SPECSFY: US-001 FR-001 NFR-002 AC-004
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]
    joined = "\n".join(dependencies)
    for removed in _REMOVED_DEPS:
        assert removed not in joined, f"dependência {removed!r} ainda declarada"
    assert any(dep.startswith("qdrant-client") for dep in dependencies)


def test_repo_has_no_chroma_or_pinecone_symbols() -> None:
    # SPECSFY: US-001 FR-001 NFR-002 AC-005
    offenders: list[str] = []
    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8")
        for symbol in _REMOVED_SYMBOLS:
            if symbol in text:
                offenders.append(f"{path.relative_to(ROOT)}::{symbol}")
    assert not offenders, f"símbolos removidos ainda presentes: {offenders}"
    vectorstores = ROOT / "src" / "pipeline" / "providers" / "vectorstores"
    assert not (vectorstores / "chroma.py").exists()
    assert not (vectorstores / "pinecone.py").exists()


def test_upsert_cli_only_accepts_qdrant() -> None:
    # SPECSFY: US-003 FR-002 FR-003 AC-007
    completed = subprocess.run(
        [sys.executable, str(ROOT / "upsert_from_chunks.py"), "--provider", "chroma"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 2
    assert "invalid choice: 'chroma'" in completed.stderr

    helptext = subprocess.run(
        [sys.executable, str(ROOT / "upsert_from_chunks.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    ).stdout
    assert "chroma" not in helptext and "pinecone" not in helptext


def test_docs_do_not_list_chroma_or_pinecone_as_active_targets() -> None:
    # SPECSFY: FR-005 NFR-002 AC-011
    # Uma menção histórica ("removido pela SPEC-0010") é esperada em texto
    # narrativo; o que não pode existir é a citação como destino vetorial
    # ativo/suportado, sem esse contexto de remoção na mesma linha.
    pages = ("docs/packages.md", "docs/integrations.md", "docs/architecture.md")
    marcador_remocao = ("spec-0010", "removid", "remoç")
    offenders: list[str] = []
    for rel in pages:
        texto = (ROOT / rel).read_text(encoding="utf-8")
        for paragrafo in texto.split("\n\n"):
            if ("ChromaDB" in paragrafo or "Pinecone" in paragrafo) and not any(
                marcador in paragrafo.lower() for marcador in marcador_remocao
            ):
                offenders.append(f"{rel}: {' '.join(paragrafo.split())[:120]}")
    assert not offenders, f"documentação ainda lista ChromaDB/Pinecone como ativos: {offenders}"


def test_contracts_module_unchanged_and_factory_surface_stable() -> None:
    # SPECSFY: US-002 FR-004 NFR-003 AC-012
    digest = hashlib.sha256(_CONTRACTS.read_bytes()).hexdigest()
    assert digest == _CONTRACTS_SHA256, "contracts.py mudou; a fatia não pode alterá-lo"

    from src.pipeline.providers.factory import ProviderFactory

    public = {name for name in vars(ProviderFactory) if not name.startswith("_")}
    assert public == {"create_embedding", "create_chat_model", "create_vector_store"}

    from src.pipeline.providers import factory

    assert "chroma" not in factory._VECTOR_STORES
    assert "pinecone" not in factory._VECTOR_STORES


def test_no_default_points_to_removed_provider() -> None:
    # SPECSFY: US-003 FR-003 NFR-001 AC-013
    import re

    pattern = re.compile(
        r"""vector_cfg\.get\(\s*["']provider["']\s*,\s*["']([a-z_]+)["']\s*\)"""
    )
    all_defaults: list[str] = []
    for rel in ("src/pipeline/indexing.py", "pipeline.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        defaults = pattern.findall(text)
        all_defaults.extend(defaults)
        assert all(value == "qdrant" for value in defaults), (
            f"{rel} ainda tem default de provider != 'qdrant': {defaults}"
        )
        assert "chroma" not in text, f"{rel} ainda menciona 'chroma'"
    assert all_defaults, "nenhum default de vector_cfg provider encontrado para conferir"
