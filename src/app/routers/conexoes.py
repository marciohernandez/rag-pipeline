"""Conexões reutilizáveis de ingestão (SPEC-0026, US-001).

Somente owner e admin administram conexões da própria equipe e projeto. A chave
é somente escrita: entra cifrada e nunca volta em nenhuma resposta.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from src.app import conexoes, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.settings import get_settings

router = APIRouter(prefix="/api/v1/conexoes", tags=["conexoes"])


class ConexaoCreate(BaseModel):
    nome: str
    tipo: str
    configuracao: dict
    segredo: str | None = None


class ConexaoUpdate(BaseModel):
    nome: str | None = None
    configuracao: dict | None = None
    segredo: str | None = None


def _http(erro: conexoes.ErroDeConexao) -> HTTPException:
    return HTTPException(status_code=erro.status_code, detail=erro.detalhe)


def _serializar(session, conexao) -> dict:
    return conexoes.serializar_conexao(conexao, repo.contar_bases_da_conexao(session, conexao.id))


def _serializar_com_teste(session, conexao) -> dict:
    """Resposta de criar e editar: a conexão gravada mais o resultado do teste (SPEC-0029)."""
    configuracoes = get_settings()
    resposta = _serializar(session, conexao)
    resposta["teste"] = conexoes.testar_conexao_salva(
        conexao,
        configuracoes.conexoes_chave,
        permitir_locais=configuracoes.conexoes_permitir_locais,
    )
    return resposta


def _cifrar(segredo: str | None, tipo: str, *, obrigatorio: bool) -> str | None:
    """Cifra a chave recebida; `None` significa que nada foi informado."""
    if segredo is None:
        if obrigatorio and tipo in {conexoes.TIPO_EMBEDDINGS, conexoes.TIPO_IA}:
            raise conexoes.ErroDeConexao("Informe a chave da conexão.")
        return None
    if not segredo.strip():
        raise conexoes.ErroDeConexao("Informe uma nova chave ou omita o campo.")
    return conexoes.cifrar_segredo(get_settings().conexoes_chave, segredo.strip())


@router.get("")
def listar(identity: Identity = Depends(get_identity)) -> list[dict]:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        return [_serializar(session, c) for c in repo.list_conexoes_for_identity(session, identity)]


@router.post("", status_code=201)
def criar(
    payload: ConexaoCreate,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    try:
        nome = conexoes.validar_nome(payload.nome)
        tipo = conexoes.validar_tipo(payload.tipo)
        configuracao = conexoes.validar_configuracao(
            tipo, payload.configuracao, permitir_locais=get_settings().conexoes_permitir_locais
        )
        cifrado = _cifrar(payload.segredo, tipo, obrigatorio=True)
    except conexoes.ErroDeConexao as erro:
        raise _http(erro) from erro
    with SessionLocal() as session:
        conexao = repo.criar_conexao(
            session,
            identity,
            nome=nome,
            tipo=tipo,
            configuracao=configuracao,
            segredo_cifrado=cifrado,
        )
        session.commit()
        return _serializar_com_teste(session, conexao)


@router.get("/{conexao_id}")
def obter(conexao_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        return _serializar(session, repo.get_conexao_or_404(session, conexao_id, identity))


@router.patch("/{conexao_id}")
def editar(
    conexao_id: str,
    payload: ConexaoUpdate,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        conexao = repo.get_conexao_or_404(session, conexao_id, identity, for_update=True)
        try:
            nome = conexoes.validar_nome(payload.nome) if payload.nome is not None else None
            configuracao = (
                conexoes.validar_configuracao(
                    conexao.tipo,
                    payload.configuracao,
                    permitir_locais=get_settings().conexoes_permitir_locais,
                )
                if payload.configuracao is not None
                else None
            )
            cifrado = _cifrar(payload.segredo, conexao.tipo, obrigatorio=False)
        except conexoes.ErroDeConexao as erro:
            raise _http(erro) from erro
        repo.atualizar_conexao(
            session,
            identity,
            conexao,
            nome=nome,
            configuracao=configuracao,
            segredo_cifrado=cifrado,
        )
        session.commit()
        return _serializar_com_teste(session, conexao)


@router.post("/{conexao_id}/desativar")
def desativar(conexao_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        conexao = repo.get_conexao_or_404(session, conexao_id, identity, for_update=True)
        repo.alterar_situacao_conexao(session, identity, conexao, "desativada")
        session.commit()
        return _serializar(session, conexao)


@router.post("/{conexao_id}/reativar")
def reativar(conexao_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        conexao = repo.get_conexao_or_404(session, conexao_id, identity, for_update=True)
        repo.alterar_situacao_conexao(session, identity, conexao, "ativa")
        session.commit()
        return _serializar(session, conexao)


@router.delete("/{conexao_id}", status_code=204)
def excluir(conexao_id: str, identity: Identity = Depends(get_identity)) -> Response:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        conexao = repo.get_conexao_or_404(session, conexao_id, identity, for_update=True)
        repo.excluir_conexao(session, identity, conexao)
        session.commit()
    return Response(status_code=204)
