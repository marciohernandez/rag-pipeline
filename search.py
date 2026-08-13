"""
Pipeline RAG — Script de Busca RAG Interativo
Permite testar consultas na base vetorial indexada.

Uso:
    uv run python search.py "qual a taxa do cheque especial?"
    uv run python search.py --k 5 "como abrir conta PJ no C6?"
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, setup_logging
from src.embedder import get_embeddings, get_vector_store

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Busca RAG na base vetorial")
    parser.add_argument("query", help="Pergunta ou consulta para buscar")
    parser.add_argument("--k", type=int, default=4, help="Número de chunks a retornar (padrão: 4)")
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    setup_logging(cfg.get("log", {}).get("level", "WARNING"))

    caminhos = cfg["caminhos"]
    embedding_cfg = cfg.get("embedding", {})
    vector_cfg = cfg.get("vector_store", {})
    persist_dir = caminhos.get("vector_store_dir", "./output/chroma_db")

    embeddings = get_embeddings(embedding_cfg)
    store = get_vector_store(vector_cfg, embeddings, persist_dir)

    print(f"\n🔍 Buscando: \"{args.query}\" (k={args.k})\n")
    results = store.similarity_search_with_score(args.query, k=args.k)

    if not results:
        print("❌ Nenhum resultado encontrado.")
        return

    print("=" * 70)
    for i, (doc, score) in enumerate(results, 1):
        nome = doc.metadata.get("nome_arquivo", "?")
        secao = doc.metadata.get("secao", "")
        titulo = doc.metadata.get("titulo", "")
        header_info = f" › {titulo}" if titulo else ""
        header_info += f" › {secao}" if secao else ""

        print(f"\n[{i}] 📄 {nome}{header_info}  (score: {score:.4f})")
        print("-" * 70)
        print(doc.page_content[:600])
        if len(doc.page_content) > 600:
            print("  ... [truncado]")
    print("=" * 70)


if __name__ == "__main__":
    main()
