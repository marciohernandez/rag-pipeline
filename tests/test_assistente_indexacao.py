"""Testes da indexação da documentação viva do assistente (SPEC-0021).

Contrato fixado: ``service.index_assistant_knowledge(config, raiz=)`` recebe a
mesma configuração de ``query_base`` (``projeto``, ``embedding``,
``vector_store``) e a raiz do repositório, e devolve as contagens ``previstos``,
``inseridos``, ``mantidos`` e ``removidos``.
"""

from __future__ import annotations

from pathlib import Path

from tests._assistente import exigir

CONFIG = {
    "projeto": {"nome": "assistente-conhecimento"},
    "embedding": {"provider": "fake", "dimensions": 16},
    "vector_store": {"provider": "qdrant", "collection_name": "assistente_conhecimento"},
}


def _escrever(raiz: Path, caminho: str, texto: str) -> None:
    destino = raiz / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")


def _repositorio(raiz: Path) -> None:
    _escrever(
        raiz,
        "docs/architecture.md",
        "# Arquitetura\n\nO fluxo de ingestão lê Markdown e faz upsert.\n",
    )
    _escrever(
        raiz, "docs/pipeline.md", "# Pipeline\n\nChunking por cabeçalhos e overlap configurável.\n"
    )
    _escrever(raiz, "PROJECT.md", "# Projeto\n\nPipeline RAG com backend e frontend.\n")
    _escrever(raiz, "INTERFACE.md", "# Interface\n\nTelas de Workspaces e Bases.\n")
    _escrever(raiz, ".specsfy/STACK.md", "# Stack\n\nPython, FastAPI e Qdrant.\n")
    _escrever(raiz, ".specsfy/DATABASE.md", "# Dados\n\nTabelas do backend de aplicação.\n")


def _adapter_compartilhado(monkeypatch):
    from src.pipeline.providers.vectorstores.in_memory import InMemoryVectorStoreAdapter

    adapter = InMemoryVectorStoreAdapter()
    monkeypatch.setattr("src.pipeline.indexing.build_vector_store", lambda *a, **k: adapter)
    return adapter


def _conta(resultado, chave: str) -> int:
    return int(getattr(resultado, chave) if hasattr(resultado, chave) else resultado[chave])


def _registros(adapter) -> dict:
    backend = adapter._resolve_backend()
    return {i: r for pontos in backend._records.values() for i, r in pontos.items()}


def test_indexar_documentacao_duas_vezes_nao_duplica_pontos(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0021 FR-011 NFR-004 AC-018"""
    service = exigir("src.pipeline.service", "index_assistant_knowledge")
    _repositorio(tmp_path)
    adapter = _adapter_compartilhado(monkeypatch)

    primeira = service(CONFIG, raiz=tmp_path)
    pontos = set(_registros(adapter))
    segunda = service(CONFIG, raiz=tmp_path)

    assert pontos and _conta(primeira, "inseridos") == len(pontos)
    assert set(_registros(adapter)) == pontos
    assert _conta(segunda, "inseridos") == 0
    assert _conta(segunda, "mantidos") == len(pontos)
    assert _conta(segunda, "removidos") == 0
    assert _conta(segunda, "previstos") == len(pontos)


def test_indexacao_le_apenas_a_lista_de_documentos_autorizados(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0021 FR-011 NFR-001 AC-022"""
    service = exigir("src.pipeline.service", "index_assistant_knowledge")
    _repositorio(tmp_path)
    _escrever(tmp_path, ".env", "OPENROUTER_API_KEY=sk-segredo-do-env\n")
    _escrever(
        tmp_path, "notas-fora-da-lista.md", "# Notas\n\nDocumento fora da lista autorizada.\n"
    )
    _escrever(tmp_path, "specs/backlog/0001-x.md", "# Backlog\n\nDado interno de spec.\n")
    adapter = _adapter_compartilhado(monkeypatch)

    service(CONFIG, raiz=tmp_path)

    registros = _registros(adapter)
    assert registros
    tudo = "\n".join(f"{r.content}\n{dict(r.metadata)}" for r in registros.values())
    assert "sk-segredo-do-env" not in tudo
    assert "fora da lista" not in tudo and "notas-fora-da-lista" not in tudo
    assert "Dado interno de spec" not in tudo
    origens = {str(r.metadata.get("caminho_origem")) for r in registros.values()}
    assert origens == {
        "docs/architecture.md",
        "docs/pipeline.md",
        "PROJECT.md",
        "INTERFACE.md",
        ".specsfy/STACK.md",
        ".specsfy/DATABASE.md",
    }
