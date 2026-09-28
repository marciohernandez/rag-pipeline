"""
Indexa a documentação viva do produto na coleção de conhecimento do assistente.

Lê somente docs/, PROJECT.md, INTERFACE.md, .specsfy/STACK.md e
.specsfy/DATABASE.md, e sincroniza os chunks de forma idempotente. Use os mesmos
valores de APP_EMBEDDING_PROVIDER, APP_EMBEDDING_DIMENSIONS e
APP_VECTOR_STORE_PROVIDER do backend, senão a busca não encontra os pontos.

Uso:
    uv run python index_assistant_docs.py
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.bootstrap import load_env
from src.pipeline import service

logger = logging.getLogger(__name__)


def build_config() -> dict:
    """Monta a configuração a partir do ambiente, espelhando `src/app/main.py`."""
    return {
        "projeto": {"nome": "assistente-conhecimento"},
        "caminhos": {},
        "embedding": {
            "provider": os.environ.get("APP_EMBEDDING_PROVIDER", "fake"),
            "dimensions": int(os.environ.get("APP_EMBEDDING_DIMENSIONS", "16")),
        },
        "vector_store": {
            "provider": os.environ.get("APP_VECTOR_STORE_PROVIDER", "qdrant"),
            "collection_name": os.environ.get(
                "APP_ASSISTANT_KNOWLEDGE_COLLECTION", "assistente_conhecimento"
            ),
        },
    }


def main() -> int:
    load_env()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    contagens = service.index_assistant_knowledge(build_config(), raiz=Path(__file__).parent)
    print(
        "Conhecimento do assistente: "
        f"previstos={contagens.previstos} inseridos={contagens.inseridos} "
        f"mantidos={contagens.mantidos} removidos={contagens.removidos}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
