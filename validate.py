"""
Pipeline RAG — Validação somente leitura de uma base indexada (SPEC-0004)

Confere, sem alterar nada no destino: conexão e escopo, correspondência entre o
manifesto e as identidades indexadas, e o comportamento de recuperação descrito
pelo gabarito da base.

Códigos de saída:
    0  base aprovada
    1  base reprovada: a validação ocorreu e encontrou divergência
    2  não foi possível validar: configuração, gabarito ou ambiente

Uso:
    uv run python validate.py
    uv run python validate.py --config config.yaml
    uv run python validate.py --tenant cliente-a
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, setup_logging
from src.validation import exit_code, validate_base

logger = logging.getLogger(__name__)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida uma base indexada sem alterá-la"
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument(
        "--tenant",
        default=None,
        help=(
            "Escopo lógico do tenant. Sem este argumento a validação alcança "
            "somente registros sem tenant."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        cfg = load_config(args.config)
    except Exception as error:  # configuração ausente ou ilegível
        print(f"Não foi possível validar: {error}")
        return 2

    setup_logging(cfg.get("log", {}).get("level", "WARNING"))
    report = validate_base(cfg, tenant_id=args.tenant)

    print(report.render())
    if report.report_path:
        print(f"\nResultado estruturado: {report.report_path}")

    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
