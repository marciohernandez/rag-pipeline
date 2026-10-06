"""Registro e retenção dos eventos de acesso da aplicação."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.app.models import EventoAcesso, EventoConexao, Sessao, TentativaLogin
from src.app.security import RETENCAO_EVENTOS

TIPOS_EVENTO = frozenset(
    {
        "entrou",
        "senha_errada",
        "bloqueada",
        "senha_trocada",
        "senha_redefinida",
        "pessoa_criada",
        "dados_corrigidos",
        "papel_alterado",
        "pessoa_desativada",
        "pessoa_reativada",
        "sessao_encerrada",
    }
)


def registrar_evento(
    sessao: Session,
    tipo: str,
    *,
    ator_pessoa_id: str | None = None,
    alvo_pessoa_id: str | None = None,
    tenant_id: str | None = None,
    project_id: str | None = None,
    motivo: str | None = None,
    criado_em: datetime | None = None,
) -> EventoAcesso:
    if tipo not in TIPOS_EVENTO:
        raise ValueError(f"Tipo de evento de acesso inválido: {tipo}")
    evento = EventoAcesso(
        tipo=tipo,
        ator_pessoa_id=ator_pessoa_id,
        alvo_pessoa_id=alvo_pessoa_id,
        tenant_id=tenant_id,
        project_id=project_id,
        motivo=motivo,
        criado_em=criado_em or datetime.now(UTC),
    )
    sessao.add(evento)
    return evento


def purgar_dados_de_acesso(sessao: Session, agora: datetime | None = None) -> dict[str, int]:
    """Apaga somente dados expirados; pessoas e autoria permanecem."""
    agora = agora or datetime.now(UTC)
    eventos = sessao.execute(
        delete(EventoAcesso).where(EventoAcesso.criado_em < agora - RETENCAO_EVENTOS)
    ).rowcount
    sessoes = sessao.execute(delete(Sessao).where(Sessao.expira_em <= agora)).rowcount
    tentativas = sessao.execute(
        delete(TentativaLogin).where(
            TentativaLogin.bloqueada_ate.is_not(None),
            TentativaLogin.bloqueada_ate <= agora,
        )
    ).rowcount
    sessao.commit()
    return {
        "eventos": max(eventos or 0, 0),
        "sessoes": max(sessoes or 0, 0),
        "tentativas": max(tentativas or 0, 0),
    }


ACOES_CONEXAO = frozenset(
    {"criada", "editada", "chave_trocada", "desativada", "reativada", "excluida"}
)


def registrar_evento_conexao(
    sessao: Session,
    acao: str,
    *,
    conexao_id: str,
    tenant_id: str,
    project_id: str,
    ator_pessoa_id: str | None,
) -> EventoConexao:
    """Registra quem fez o quê numa conexão; nunca recebe valores nem segredos."""
    if acao not in ACOES_CONEXAO:
        raise ValueError(f"Ação de conexão inválida: {acao}")
    evento = EventoConexao(
        acao=acao,
        conexao_id=conexao_id,
        tenant_id=tenant_id,
        project_id=project_id,
        ator_pessoa_id=ator_pessoa_id,
    )
    sessao.add(evento)
    return evento


def purgar_eventos_conexao(sessao: Session, agora: datetime | None = None) -> int:
    """Apaga somente eventos de conexão mais antigos que a retenção de 90 dias."""
    agora = agora or datetime.now(UTC)
    removidos = sessao.execute(
        delete(EventoConexao).where(EventoConexao.criado_em < agora - RETENCAO_EVENTOS)
    ).rowcount
    sessao.commit()
    return max(removidos or 0, 0)
