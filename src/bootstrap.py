"""Bootstrap de ambiente dos entrypoints da raiz (SPEC-0009).

Ponto único de carga do `.env`. Os comandos de linha de comando da raiz chamam
`load_env()` como primeira ação de `main()`; o código de biblioteca sob
`src/pipeline/` nunca carrega o `.env` — apenas lê variáveis já presentes no
ambiente.
"""

from __future__ import annotations

from dotenv import load_dotenv


def load_env() -> None:
    """Carrega o `.env` do diretório de trabalho para o ambiente do processo.

    Idempotente e sem sobrescrever variável já definida: `load_dotenv()` sem
    `override` preserva o que o ambiente (CI, shell) já traz. Não levanta erro
    quando não há arquivo `.env`.
    """
    load_dotenv()
