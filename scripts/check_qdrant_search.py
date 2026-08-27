"""Executa uma busca semantica de leitura na collection Qdrant configurada."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from check_qdrant_connection import load_env, request_json


TIMEOUT_SECONDS = 30
DEFAULT_QUERY = "Como ganhar Vale Bonus sendo cliente Vivo Fibra?"


def read_yaml_section(path: Path, section: str) -> dict[str, str]:
    """Le os escalares simples usados neste teste sem depender de PyYAML."""
    values: dict[str, str] = {}
    inside_section = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line and not raw_line[0].isspace():
            inside_section = raw_line.strip() == f"{section}:"
            continue
        if not inside_section:
            continue

        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        name, value = line.split(":", 1)
        values[name.strip()] = value.strip().strip("\"'")

    return values


def create_embedding(api_key: str, model: str, dimensions: int, query: str) -> list[float]:
    body = json.dumps(
        {"model": model, "input": query, "dimensions": dimensions}
    ).encode("utf-8")
    request = Request(
        "https://api.openai.com/v1/embeddings",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        result = json.load(response)
    return result["data"][0]["embedding"]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_env(project_root / ".env")
    embedding_config = read_yaml_section(project_root / "config.yaml", "embedding")
    vector_config = read_yaml_section(project_root / "config.yaml", "vector_store")

    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY
    provider = vector_config.get("provider")
    collection = vector_config.get("collection_name")
    embedding_provider = embedding_config.get("provider")
    model = embedding_config.get("model", "text-embedding-3-small")
    dimensions = int(embedding_config.get("dimensions", "1536"))

    if provider != "qdrant":
        print(f"Configuracao invalida: vector_store.provider={provider!r}")
        return 2
    if embedding_provider != "openai":
        print(f"Teste REST ainda nao suporta embedding.provider={embedding_provider!r}")
        return 2

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    qdrant_url = os.getenv("QDRANT_URL", "").strip()
    qdrant_key = os.getenv("QDRANT_API_KEY", "").strip()
    if not all((openai_key, qdrant_url, qdrant_key, collection)):
        print("Faltam credenciais ou o nome da collection.")
        return 2

    print(f"Consulta: {query}", flush=True)
    print(f"Embedding: {model} ({dimensions} dimensoes)", flush=True)
    print(f"Collection: {collection}", flush=True)

    try:
        vector = create_embedding(openai_key, model, dimensions, query)
        print(f"Embedding gerado: {len(vector)} dimensoes", flush=True)

        response = request_json(
            qdrant_url,
            qdrant_key,
            f"/collections/{collection}/points/search",
            {"vector": vector, "limit": 3, "with_payload": True},
        )
        results = response.get("result", [])
        print(f"Resultados recuperados: {len(results)}")

        for position, result in enumerate(results, start=1):
            payload = result.get("payload", {})
            metadata = payload.get("metadata", {})
            content = payload.get("page_content", "")
            filename = metadata.get("nome_arquivo", "<sem nome>")
            snippet = " ".join(str(content).split())[:350]
            print(f"\n[{position}] score={result.get('score', 0):.4f} | {filename}")
            print(snippet)
        return 0 if results else 1
    except HTTPError as error:
        service = "OpenAI" if "api.openai.com" in error.url else "Qdrant"
        print(f"Falha HTTP no {service}: {error.code}")
        return 1
    except (URLError, TimeoutError) as error:
        print(f"Falha de rede: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
