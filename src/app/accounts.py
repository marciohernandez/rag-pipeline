"""Casos de uso de autenticação, sessão e gestão de pessoas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.app import repo
from src.app.auth import Identity
from src.app.events import registrar_evento
from src.app.models import Pessoa, Sessao, TentativaLogin, VinculoPessoa
from src.app.security import (
    DURACAO_BLOQUEIO,
    DURACAO_SESSAO,
    MAX_FALHAS_LOGIN,
    SenhaInvalida,
    gerar_token_sessao,
    hash_senha,
    resumir_token,
    validar_politica_senha,
    verificar_senha,
)

PAPEIS = frozenset({"owner", "admin", "member"})


@dataclass(frozen=True)
class AccountError(Exception):
    status_code: int
    detail: str | dict[str, str]


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def _agora() -> datetime:
    return datetime.now(UTC)


def _validar_nome(nome: str) -> str:
    nome = nome.strip()
    if not nome:
        raise AccountError(422, {"campo": "nome", "mensagem": "Informe o nome."})
    return nome


def _validar_email(email: str) -> str:
    email = normalizar_email(email)
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise AccountError(422, {"campo": "email", "mensagem": "Informe um e-mail válido."})
    return email


def _validar_papel(papel: str) -> str:
    if papel not in PAPEIS:
        raise AccountError(422, {"campo": "papel", "mensagem": "Papel inválido."})
    return papel


def serializar_pessoa(
    session: Session, pessoa: Pessoa, vinculo: VinculoPessoa
) -> dict[str, Any]:
    criadora = session.get(Pessoa, pessoa.criada_por) if pessoa.criada_por else None
    return {
        "id": pessoa.id,
        "nome": pessoa.nome,
        "email": pessoa.email,
        "papel": vinculo.papel,
        "tenant_id": vinculo.tenant_id,
        "project_id": vinculo.project_id,
        "situacao": pessoa.situacao,
        "precisa_trocar_senha": pessoa.precisa_trocar_senha,
        "criada_em": pessoa.criada_em.isoformat(),
        "criada_por": (
            {"id": criadora.id, "nome": criadora.nome, "desativada": criadora.situacao != "ativa"}
            if criadora is not None
            else None
        ),
    }


def _vinculo_da_pessoa(session: Session, pessoa_id: str) -> VinculoPessoa:
    vinculo = session.execute(
        select(VinculoPessoa).where(VinculoPessoa.pessoa_id == pessoa_id)
    ).scalar_one()
    return vinculo


def _registrar_falha_login(
    session: Session, email: str, pessoa: Pessoa | None, agora: datetime
) -> None:
    tentativa = session.get(TentativaLogin, email)
    if tentativa is None:
        tentativa = TentativaLogin(email_normalizado=email, falhas_seguidas=0, atualizada_em=agora)
        session.add(tentativa)
    tentativa.falhas_seguidas += 1
    tentativa.atualizada_em = agora
    vinculo = _vinculo_da_pessoa(session, pessoa.id) if pessoa is not None else None
    registrar_evento(
        session,
        "senha_errada",
        alvo_pessoa_id=pessoa.id if pessoa is not None else None,
        tenant_id=vinculo.tenant_id if vinculo is not None else None,
        project_id=vinculo.project_id if vinculo is not None else None,
    )
    if tentativa.falhas_seguidas >= MAX_FALHAS_LOGIN:
        tentativa.bloqueada_ate = agora + DURACAO_BLOQUEIO
        registrar_evento(
            session,
            "bloqueada",
            alvo_pessoa_id=pessoa.id if pessoa is not None else None,
            tenant_id=vinculo.tenant_id if vinculo is not None else None,
            project_id=vinculo.project_id if vinculo is not None else None,
        )


def entrar(session: Session, email: str, senha: str) -> tuple[str, Sessao, Pessoa, VinculoPessoa]:
    agora = _agora()
    email = normalizar_email(email)
    tentativa = session.get(TentativaLogin, email)
    if tentativa is not None and tentativa.bloqueada_ate is not None:
        if tentativa.bloqueada_ate > agora:
            pessoa_bloqueada = repo.get_pessoa_by_email(session, email)
            vinculo = (
                _vinculo_da_pessoa(session, pessoa_bloqueada.id)
                if pessoa_bloqueada is not None
                else None
            )
            registrar_evento(
                session,
                "bloqueada",
                alvo_pessoa_id=pessoa_bloqueada.id if pessoa_bloqueada else None,
                tenant_id=vinculo.tenant_id if vinculo else None,
                project_id=vinculo.project_id if vinculo else None,
            )
            session.commit()
            raise AccountError(
                429, "Entrada temporariamente bloqueada. Tente novamente mais tarde."
            )
        session.delete(tentativa)
        session.flush()

    pessoa = repo.get_pessoa_by_email(session, email)
    senha_correta = verificar_senha(pessoa.senha_hash if pessoa is not None else None, senha)
    if pessoa is None or not senha_correta or pessoa.situacao != "ativa":
        _registrar_falha_login(session, email, pessoa, agora)
        session.commit()
        raise AccountError(401, "Credenciais inválidas.")

    vinculo = _vinculo_da_pessoa(session, pessoa.id)
    session.execute(delete(TentativaLogin).where(TentativaLogin.email_normalizado == email))
    token = gerar_token_sessao()
    sessao = Sessao(
        pessoa_id=pessoa.id,
        token_hash=resumir_token(token),
        criada_em=agora,
        expira_em=agora + DURACAO_SESSAO,
    )
    session.add(sessao)
    registrar_evento(
        session,
        "entrou",
        ator_pessoa_id=pessoa.id,
        alvo_pessoa_id=pessoa.id,
        tenant_id=vinculo.tenant_id,
        project_id=vinculo.project_id,
    )
    session.commit()
    return token, sessao, pessoa, vinculo


def encerrar_sessoes(
    session: Session,
    pessoa_id: str,
    *,
    motivo: str,
    ator: Identity | None = None,
    preservar_sessao_id: str | None = None,
) -> None:
    stmt = delete(Sessao).where(Sessao.pessoa_id == pessoa_id)
    if preservar_sessao_id is not None:
        stmt = stmt.where(Sessao.id != preservar_sessao_id)
    session.execute(stmt)
    vinculo = _vinculo_da_pessoa(session, pessoa_id)
    registrar_evento(
        session,
        "sessao_encerrada",
        ator_pessoa_id=ator.person_id if ator else pessoa_id,
        alvo_pessoa_id=pessoa_id,
        tenant_id=vinculo.tenant_id,
        project_id=vinculo.project_id,
        motivo=motivo,
    )


def sair(session: Session, identity: Identity) -> None:
    sessao = session.get(Sessao, identity.session_id)
    if sessao is not None:
        session.delete(sessao)
        registrar_evento(
            session,
            "sessao_encerrada",
            ator_pessoa_id=identity.person_id,
            alvo_pessoa_id=identity.person_id,
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
            motivo="logout",
        )
        session.commit()


def trocar_senha(
    session: Session,
    identity: Identity,
    *,
    nova_senha: str,
    senha_atual: str | None = None,
) -> None:
    pessoa = session.get(Pessoa, identity.person_id)
    if pessoa is None:
        raise AccountError(401, "Sessão inválida.")
    if not pessoa.precisa_trocar_senha and (
        not senha_atual or not verificar_senha(pessoa.senha_hash, senha_atual)
    ):
        raise AccountError(
            422, {"campo": "senha_atual", "mensagem": "Senha atual incorreta."}
        )
    try:
        validar_politica_senha(nova_senha, senha_atual=senha_atual)
    except SenhaInvalida as erro:
        raise AccountError(422, {"campo": "nova_senha", "mensagem": str(erro)}) from erro
    if verificar_senha(pessoa.senha_hash, nova_senha):
        raise AccountError(
            422, {"campo": "nova_senha", "mensagem": "A nova senha deve ser diferente da atual."}
        )
    pessoa.senha_hash = hash_senha(nova_senha)
    pessoa.precisa_trocar_senha = False
    pessoa.atualizada_em = _agora()
    encerrar_sessoes(
        session,
        pessoa.id,
        motivo="senha_trocada",
        ator=identity,
        preservar_sessao_id=identity.session_id,
    )
    registrar_evento(
        session,
        "senha_trocada",
        ator_pessoa_id=pessoa.id,
        alvo_pessoa_id=pessoa.id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
    )
    session.commit()


def _exigir_gestor(identity: Identity) -> None:
    if identity.role not in {"owner", "admin"}:
        raise AccountError(403, "Permissão insuficiente para administrar pessoas.")


def _proteger_owner(
    identity: Identity, vinculo_alvo: VinculoPessoa, novo_papel: str | None = None
) -> None:
    if identity.role == "admin" and (
        vinculo_alvo.papel == "owner" or novo_papel == "owner"
    ):
        raise AccountError(403, "Admin não pode administrar owner.")


def criar_pessoa(
    session: Session,
    identity: Identity,
    *,
    nome: str,
    email: str,
    papel: str,
    senha_inicial: str,
) -> tuple[Pessoa, VinculoPessoa]:
    _exigir_gestor(identity)
    papel = _validar_papel(papel)
    if identity.role == "admin" and papel == "owner":
        raise AccountError(403, "Admin não pode criar owner.")
    try:
        senha_hash = hash_senha(senha_inicial)
    except SenhaInvalida as erro:
        raise AccountError(422, {"campo": "senha_inicial", "mensagem": str(erro)}) from erro
    pessoa = Pessoa(
        nome=_validar_nome(nome),
        email=_validar_email(email),
        senha_hash=senha_hash,
        precisa_trocar_senha=True,
        situacao="ativa",
        criada_por=identity.person_id,
    )
    vinculo = VinculoPessoa(
        pessoa=pessoa,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        papel=papel,
    )
    session.add_all([pessoa, vinculo])
    try:
        session.flush()
        registrar_evento(
            session,
            "pessoa_criada",
            ator_pessoa_id=identity.person_id,
            alvo_pessoa_id=pessoa.id,
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
        )
        session.commit()
    except IntegrityError as erro:
        session.rollback()
        raise AccountError(409, "Este e-mail já está em uso. Informe outro e-mail.") from erro
    return pessoa, vinculo


def atualizar_pessoa(
    session: Session,
    identity: Identity,
    pessoa_id: str,
    *,
    nome: str | None = None,
    email: str | None = None,
    papel: str | None = None,
) -> tuple[Pessoa, VinculoPessoa]:
    _exigir_gestor(identity)
    quantidade_owners_ativos = repo.count_active_owners_for_update(
        session, identity.tenant_id, identity.project_id
    )
    pessoa, vinculo = repo.get_pessoa_or_404(session, pessoa_id, identity, for_update=True)
    papel_validado = _validar_papel(papel) if papel is not None else None
    _proteger_owner(identity, vinculo, papel_validado)
    if (
        vinculo.papel == "owner"
        and papel_validado is not None
        and papel_validado != "owner"
        and quantidade_owners_ativos <= 1
    ):
        raise AccountError(409, "O último owner ativo não pode ser rebaixado.")

    dados_mudaram = False
    papel_mudou = papel_validado is not None and papel_validado != vinculo.papel
    if nome is not None:
        nome_validado = _validar_nome(nome)
        dados_mudaram = dados_mudaram or nome_validado != pessoa.nome
        pessoa.nome = nome_validado
    if email is not None:
        email_validado = _validar_email(email)
        dados_mudaram = dados_mudaram or email_validado != pessoa.email
        pessoa.email = email_validado
    if papel_validado is not None:
        vinculo.papel = papel_validado
    pessoa.atualizada_em = _agora()
    if dados_mudaram or papel_mudou:
        encerrar_sessoes(
            session,
            pessoa.id,
            motivo="papel_alterado" if papel_mudou else "dados_corrigidos",
            ator=identity,
            preservar_sessao_id=identity.session_id if identity.person_id == pessoa.id else None,
        )
    if dados_mudaram:
        registrar_evento(
            session,
            "dados_corrigidos",
            ator_pessoa_id=identity.person_id,
            alvo_pessoa_id=pessoa.id,
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
        )
    if papel_mudou:
        registrar_evento(
            session,
            "papel_alterado",
            ator_pessoa_id=identity.person_id,
            alvo_pessoa_id=pessoa.id,
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
        )
    try:
        session.commit()
    except IntegrityError as erro:
        session.rollback()
        raise AccountError(409, "Este e-mail já está em uso. Informe outro e-mail.") from erro
    return pessoa, vinculo


def desativar_pessoa(session: Session, identity: Identity, pessoa_id: str) -> None:
    _exigir_gestor(identity)
    if pessoa_id == identity.person_id:
        raise AccountError(409, "Você não pode desativar a própria conta.")
    quantidade_owners_ativos = repo.count_active_owners_for_update(
        session, identity.tenant_id, identity.project_id
    )
    pessoa, vinculo = repo.get_pessoa_or_404(session, pessoa_id, identity, for_update=True)
    _proteger_owner(identity, vinculo)
    if (
        vinculo.papel == "owner"
        and pessoa.situacao == "ativa"
        and quantidade_owners_ativos <= 1
    ):
        raise AccountError(409, "O último owner ativo não pode ser desativado.")
    pessoa.situacao = "desativada"
    pessoa.atualizada_em = _agora()
    encerrar_sessoes(session, pessoa.id, motivo="pessoa_desativada", ator=identity)
    registrar_evento(
        session,
        "pessoa_desativada",
        ator_pessoa_id=identity.person_id,
        alvo_pessoa_id=pessoa.id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
    )
    session.commit()


def reativar_pessoa(session: Session, identity: Identity, pessoa_id: str) -> None:
    _exigir_gestor(identity)
    pessoa, vinculo = repo.get_pessoa_or_404(session, pessoa_id, identity, for_update=True)
    _proteger_owner(identity, vinculo)
    pessoa.situacao = "ativa"
    pessoa.atualizada_em = _agora()
    registrar_evento(
        session,
        "pessoa_reativada",
        ator_pessoa_id=identity.person_id,
        alvo_pessoa_id=pessoa.id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
    )
    session.commit()


def redefinir_senha(
    session: Session, identity: Identity, pessoa_id: str, senha_temporaria: str
) -> None:
    _exigir_gestor(identity)
    pessoa, vinculo = repo.get_pessoa_or_404(session, pessoa_id, identity, for_update=True)
    _proteger_owner(identity, vinculo)
    try:
        pessoa.senha_hash = hash_senha(senha_temporaria)
    except SenhaInvalida as erro:
        raise AccountError(422, {"campo": "senha_temporaria", "mensagem": str(erro)}) from erro
    pessoa.precisa_trocar_senha = True
    pessoa.atualizada_em = _agora()
    encerrar_sessoes(session, pessoa.id, motivo="senha_redefinida", ator=identity)
    session.execute(
        delete(TentativaLogin).where(
            TentativaLogin.email_normalizado == normalizar_email(pessoa.email)
        )
    )
    registrar_evento(
        session,
        "senha_redefinida",
        ator_pessoa_id=identity.person_id,
        alvo_pessoa_id=pessoa.id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
    )
    session.commit()
