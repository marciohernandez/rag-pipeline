"""Entrypoint do worker Procrastinate (SPEC-0012, seção 8).

``python -m procrastinate --app src.app.tasks.app worker`` sozinho **não**
processa a fila: ``src.app.tasks.app`` nasce com ``InMemoryConnector`` e só o
entrypoint HTTP (``src.app.main``) o religa ao PostgreSQL via
``configure_connector`` (um ``procrastinate.PsycopgConnector`` real). Um worker
fora do processo da API precisa da mesma fiação.

Importar ``src.app.main`` aqui aplica essa fiação como efeito colateral
(resolve ``APP_DATABASE_URL``, configura ``db``/``settings``/``storage`` e troca
o connector do Procrastinate) antes de expor ``app``. Rode o worker com:

    uv run python -m src.app.worker
"""

from __future__ import annotations

import src.app.main  # noqa: F401 — efeito colateral: configure_connector(PsycopgConnector real)
from src.app.tasks import app

__all__ = ["app"]


if __name__ == "__main__":
    app.run_worker(wait=True)
