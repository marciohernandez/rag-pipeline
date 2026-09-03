"""
Pipeline RAG — Diagnóstico de qualidade da preparação (SPEC-0006)

Avalia, sem tocar no destino remoto, um arquivo de chunks já gerado: os
invariantes críticos de integridade e os sinais de qualidade agrupados por
documento de origem.

Como não há manifesto neste modo, o invariante de contagem é pulado e o
relatório declara o salto; os outros cinco continuam sendo avaliados.

Códigos de saída:
    0  conjunto aprovado
    1  conjunto reprovado: um invariante crítico falhou
    2  não foi possível avaliar: arquivo ausente, ilegível ou malformado

Uso:
    uv run python quality.py
    uv run python quality.py --chunks ./output/base/chunks.json
    uv run python quality.py --config config.yaml --output-dir ./output/base
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.documents import Document

from src.config import load_config, setup_logging
from src.quality import QualityGateError, evaluate_quality

logger = logging.getLogger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Avalia a qualidade de um conjunto de chunks sem indexar"
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument(
        "--chunks",
        default=None,
        help=(
            "Arquivo de chunks a avaliar. Sem este argumento, usa "
            "caminhos.chunks_file da configuração."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Diretório do resultado estruturado. Sem este argumento, usa o "
            "diretório do próprio arquivo de chunks."
        ),
    )
    return parser.parse_args(argv)


def carregar_chunks(caminho: Path) -> list[Document]:
    """Lê o arquivo produzido por ``src.exporter`` e devolve os chunks.

    Levanta ``ValueError`` quando o arquivo não tem a forma esperada; a
    fronteira CLI converte isso no código de saída 2.
    """
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, list):
        raise ValueError("O arquivo de chunks precisa conter uma lista.")
    chunks: list[Document] = []
    for entrada in dados:
        if not isinstance(entrada, dict) or "content" not in entrada:
            raise ValueError("Cada entrada precisa ter o campo content.")
        chunks.append(
            Document(
                page_content=entrada["content"],
                metadata=dict(entrada.get("metadata") or {}),
            )
        )
    return chunks


def main(argv=None) -> int:
    args = parse_args(argv)

    cfg: dict = {}
    aviso_de_config = None
    try:
        cfg = load_config(args.config)
    except Exception as error:  # noqa: BLE001 - fronteira CLI decide o código de saída
        # A configuração é opcional quando o arquivo de chunks é informado:
        # ela só fornece limiares, e todos têm padrão documentado.
        if args.chunks is None:
            print(f"Não foi possível avaliar: {error}")
            return 2
        aviso_de_config = f"Configuração não carregada ({args.config}); usando padrões."

    setup_logging(cfg.get("log", {}).get("level", "WARNING"))

    caminho_dos_chunks = args.chunks or cfg.get("caminhos", {}).get("chunks_file")
    if not caminho_dos_chunks:
        print("Não foi possível avaliar: nenhum arquivo de chunks informado.")
        return 2

    caminho = Path(caminho_dos_chunks)
    try:
        chunks = carregar_chunks(caminho)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Não foi possível avaliar: {error}")
        return 2

    output_dir = Path(args.output_dir) if args.output_dir else caminho.parent

    try:
        report = evaluate_quality(
            chunks,
            cfg.get("chunking", {}),
            cfg.get("qualidade", {}),
            manifest=None,
            output_dir=output_dir,
        )
    except QualityGateError as error:
        print("Gate de qualidade da preparação")
        print("Desfecho: reprovado")
        print(f"Impedimento: {error}")
        return 1

    if aviso_de_config:
        print(f"Aviso: {aviso_de_config}")
    print(report.render())
    if report.report_path:
        print(f"\nResultado estruturado: {report.report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
