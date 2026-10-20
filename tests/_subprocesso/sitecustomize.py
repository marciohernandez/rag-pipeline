"""Carregado automaticamente por subprocessos Python dos testes (via PYTHONPATH).

Reaplica a conversão de `options` em `SET` (ver tests/_pooler_options.py), para
que o Alembic e afins respeitem o schema isolado também no pooler do Supabase.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests import _pooler_options

_pooler_options.instalar()
