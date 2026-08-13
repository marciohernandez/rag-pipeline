"""
Pipeline RAG — Módulo de Configuração
Carrega config.yaml e variáveis de ambiente com validação.
"""

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """Carrega e valida o config.yaml."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path.resolve()}")

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    logger.debug("config.yaml carregado com sucesso.")
    return cfg


def get_openai_api_key() -> str:
    """Retorna a chave da OpenAI, lançando erro se ausente."""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key.startswith("sk-..."):
        raise EnvironmentError(
            "OPENAI_API_KEY não configurada. Defina no arquivo .env ou variável de ambiente."
        )
    return key


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """Configura logging estruturado com formato padronizado."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )
    logger.info("Logging configurado. Nível: %s", level)
