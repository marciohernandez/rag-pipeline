"""Aplica o parâmetro `options` da conexão como `SET` após conectar.

Poolers como o Session pooler do Supabase (Supavisor) ignoram `options` no
startup (ex.: `-csearch_path=<schema>`), o que quebraria o isolamento por
schema da suíte. Aqui cada `-c chave=valor` vira um `SET` na própria sessão,
que o Session pooler preserva. Em Postgres comum o efeito é idêntico.
"""

from __future__ import annotations

import re

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

_PAR = re.compile(r"-c\s*([A-Za-z_.]+)=(\S+)")
_instalado = False


def _parametros(conninfo, kwargs):
    try:
        dados = conninfo_to_dict(conninfo or "", **kwargs)
    except psycopg.ProgrammingError:
        return []
    return _PAR.findall(str(dados.get("options") or ""))


def _comandos(pares):
    return [
        sql.SQL("SELECT set_config({}, {}, false)").format(sql.Literal(chave), sql.Literal(valor))
        for chave, valor in pares
    ]


def instalar() -> None:
    global _instalado
    if _instalado:
        return
    _instalado = True
    sincrono = psycopg.Connection.connect.__func__
    assincrono = psycopg.AsyncConnection.connect.__func__

    def connect(cls, conninfo="", *args, **kwargs):
        conexao = sincrono(cls, conninfo, *args, **kwargs)
        for comando in _comandos(_parametros(conninfo, kwargs)):
            conexao.execute(comando)
        if not conexao.autocommit and conexao.info.transaction_status != 0:
            conexao.commit()
        return conexao

    async def aconnect(cls, conninfo="", *args, **kwargs):
        conexao = await assincrono(cls, conninfo, *args, **kwargs)
        for comando in _comandos(_parametros(conninfo, kwargs)):
            await conexao.execute(comando)
        if not conexao.autocommit and conexao.info.transaction_status != 0:
            await conexao.commit()
        return conexao

    psycopg.Connection.connect = classmethod(connect)
    psycopg.AsyncConnection.connect = classmethod(aconnect)
    # `psycopg.connect` é uma referência capturada na importação do pacote.
    psycopg.connect = psycopg.Connection.connect
