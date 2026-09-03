"""
Pipeline RAG — Script de Busca RAG Interativo
Permite testar consultas na base vetorial indexada.

A recuperação é sempre escopada: `project_id` vem de `projeto.nome` e o
`tenant_id` é um argumento explícito. Omitir `--tenant` alcança somente os
registros sem tenant — nunca equivale a consultar sem filtro.

Uso:
    uv run python search.py "quais informações estão disponíveis?"
    uv run python search.py --k 5 "qual documento explica este assunto?"
    uv run python search.py --tenant cliente-a "qual o prazo de entrega?"
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import service
from src.pipeline.config import load_config, setup_logging
from src.pipeline.indexing import resolve_identity

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Busca RAG na base vetorial")
    parser.add_argument("query", help="Pergunta ou consulta para buscar")
    parser.add_argument("--k", type=int, default=4, help="Número de chunks a retornar (padrão: 4)")
    parser.add_argument(
        "--tenant",
        default=None,
        help=(
            "Escopo lógico do tenant. Sem este argumento a busca alcança "
            "somente registros sem tenant."
        ),
    )
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    setup_logging(cfg.get("log", {}).get("level", "WARNING"))
    identidade = resolve_identity(cfg)

    tenant_id = args.tenant.strip() if isinstance(args.tenant, str) else None
    escopo_legivel = identidade.nome + (
        f" › tenant {tenant_id}" if tenant_id else " › sem tenant"
    )
    print(f"\n🔍 Buscando: \"{args.query}\" (k={args.k}) em {escopo_legivel}\n")
    results = service.query_base(
        config=cfg,
        query=args.query,
        top_k=args.k,
        tenant_id=tenant_id,
    )

    if not results:
        print("❌ Nenhum resultado encontrado.")
        return

    print("=" * 70)
    for i, result in enumerate(results, 1):
        nome = result.metadata.get("nome_arquivo", "?")
        secao = result.metadata.get("secao", "")
        titulo = result.metadata.get("titulo", "")
        header_info = f" › {titulo}" if titulo else ""
        header_info += f" › {secao}" if secao else ""

        print(f"\n[{i}] 📄 {nome}{header_info}  (score: {result.score:.4f})")
        print("-" * 70)
        print(result.content[:600])
        if len(result.content) > 600:
            print("  ... [truncado]")
    print("=" * 70)


if __name__ == "__main__":
    main()
