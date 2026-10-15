"""Leituras com isolamento por tenant/projeto (SPEC-0012, FR-006/FR-007/AC-009)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from src.app.auth import Identity
from src.app.events import registrar_evento_conexao
from src.app.models import (
    Base,
    Colecao,
    Conexao,
    ConteudoDocumento,
    ConversaAssistente,
    DocumentoColecao,
    DocumentoConversao,
    Envio,
    LoteConversao,
    MensagemAssistente,
    Pessoa,
    VinculoPessoa,
    Workspace,
)

__all__ = [
    "alterar_situacao_conexao",
    "apagar_conteudo_do_documento",
    "apagar_conteudos_da_colecao",
    "atualizar_conexao",
    "contar_bases_da_conexao",
    "count_active_owners_for_update",
    "criar_conexao",
    "excluir_conexao",
    "get_colecao_or_404",
    "get_conexao_or_404",
    "get_conversa_or_404",
    "get_documento_or_404",
    "get_envio_or_404",
    "get_lote_or_404",
    "get_pessoa_by_email",
    "get_pessoa_or_404",
    "get_workspace_or_404",
    "has_active_bases_for_workspace",
    "has_active_colecoes_for_workspace",
    "has_envio_ativo",
    "list_colecoes_for_workspace",
    "list_conexoes_for_identity",
    "list_conversas_da_pessoa",
    "list_documentos_da_colecao",
    "list_envios_da_colecao",
    "list_lotes_for_identity",
    "list_mensagens_recentes",
    "list_pessoas_for_identity",
    "list_workspaces_for_identity",
    "obter_conteudo",
    "recalcular_situacao_lote",
    "salvar_conteudo",
]

_SITUACOES_DOCUMENTO_ATIVAS = ("fila", "processando")

_LIMITE_HISTORICO = 50
_JANELA_DE_MENSAGENS = 20


def get_workspace_or_404(session: Session, workspace_id: str, identity: Identity) -> Workspace:
    workspace = session.get(Workspace, workspace_id)
    if (
        workspace is None
        or workspace.apagada_em is not None
        or workspace.tenant_id != identity.tenant_id
        or workspace.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Workspace não encontrado.")
    return workspace


def get_pessoa_by_email(session: Session, email_normalizado: str) -> Pessoa | None:
    return session.execute(
        select(Pessoa).where(func.lower(Pessoa.email) == email_normalizado)
    ).scalar_one_or_none()


def get_pessoa_or_404(
    session: Session, pessoa_id: str, identity: Identity, *, for_update: bool = False
) -> tuple[Pessoa, VinculoPessoa]:
    stmt = (
        select(Pessoa, VinculoPessoa)
        .join(VinculoPessoa, VinculoPessoa.pessoa_id == Pessoa.id)
        .where(
            Pessoa.id == pessoa_id,
            VinculoPessoa.tenant_id == identity.tenant_id,
            VinculoPessoa.project_id == identity.project_id,
        )
    )
    if for_update:
        stmt = stmt.with_for_update()
    linha = session.execute(stmt).one_or_none()
    if linha is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    return linha[0], linha[1]


def list_pessoas_for_identity(
    session: Session, identity: Identity
) -> list[tuple[Pessoa, VinculoPessoa]]:
    stmt = (
        select(Pessoa, VinculoPessoa)
        .join(VinculoPessoa, VinculoPessoa.pessoa_id == Pessoa.id)
        .where(
            VinculoPessoa.tenant_id == identity.tenant_id,
            VinculoPessoa.project_id == identity.project_id,
        )
        .order_by(Pessoa.nome, Pessoa.id)
    )
    return [(linha[0], linha[1]) for linha in session.execute(stmt).all()]


def count_active_owners_for_update(session: Session, tenant_id: str, project_id: str) -> int:
    """Conta owners ativos depois de travar todas as linhas correspondentes."""
    stmt = (
        select(VinculoPessoa.id)
        .join(Pessoa, Pessoa.id == VinculoPessoa.pessoa_id)
        .where(
            VinculoPessoa.tenant_id == tenant_id,
            VinculoPessoa.project_id == project_id,
            VinculoPessoa.papel == "owner",
            Pessoa.situacao == "ativa",
        )
        .order_by(VinculoPessoa.id)
        .with_for_update()
    )
    return len(session.execute(stmt).scalars().all())


def list_workspaces_for_identity(session: Session, identity: Identity) -> list[Workspace]:
    stmt = (
        select(Workspace)
        .options(selectinload(Workspace.autor))
        .where(
            Workspace.tenant_id == identity.tenant_id,
            Workspace.project_id == identity.project_id,
            Workspace.apagada_em.is_(None),
        )
        .order_by(Workspace.criado_em.desc(), Workspace.id.desc())
    )
    return list(session.execute(stmt).scalars().all())


def has_active_bases_for_workspace(session: Session, workspace_id: str) -> bool:
    stmt = (
        select(Base.id).where(Base.workspace_id == workspace_id, Base.apagada_em.is_(None)).limit(1)
    )
    return session.execute(stmt).first() is not None


def list_lotes_for_identity(
    session: Session, identity: Identity, workspace_id: str | None = None
) -> list[LoteConversao]:
    """Lotes de conversão do tenant/projeto, mais recentes primeiro (SPEC-0023)."""
    filtros = [
        LoteConversao.tenant_id == identity.tenant_id,
        LoteConversao.project_id == identity.project_id,
    ]
    if workspace_id is not None:
        filtros.append(LoteConversao.workspace_id == workspace_id)
    return (
        session.execute(
            select(LoteConversao).where(*filtros).order_by(LoteConversao.criado_em.desc())
        )
        .scalars()
        .all()
    )


def get_lote_or_404(session: Session, lote_id: str, identity: Identity) -> LoteConversao:
    lote = session.get(LoteConversao, lote_id)
    if (
        lote is None
        or lote.tenant_id != identity.tenant_id
        or lote.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Lote de conversão não encontrado.")
    return lote


def get_documento_or_404(
    session: Session, lote_id: str, documento_id: str, identity: Identity
) -> DocumentoConversao:
    get_lote_or_404(session, lote_id, identity)
    documento = session.get(DocumentoConversao, documento_id)
    if documento is None or documento.lote_id != lote_id:
        raise HTTPException(status_code=404, detail="Documento de conversão não encontrado.")
    return documento


def recalcular_situacao_lote(session: Session, lote_id: str) -> None:
    """Recalcula ``LoteConversao.situacao`` a partir dos documentos filhos.

    Não comita: chamada dentro da mesma transação que atualiza o documento
    processado, ao final de ``process_conversion_document_task`` (seção 8).
    """
    lote = session.get(LoteConversao, lote_id)
    if lote is None:
        return
    situacoes = (
        session.execute(
            select(DocumentoConversao.situacao).where(DocumentoConversao.lote_id == lote_id)
        )
        .scalars()
        .all()
    )
    if any(situacao in _SITUACOES_DOCUMENTO_ATIVAS for situacao in situacoes):
        lote.situacao = "processando"
    elif any(situacao == "falhou" for situacao in situacoes):
        lote.situacao = "concluido_com_falhas"
    else:
        lote.situacao = "concluido"


def list_conversas_da_pessoa(
    session: Session, identity: Identity, limite: int = _LIMITE_HISTORICO
) -> list[ConversaAssistente]:
    """Conversas da própria pessoa, da mais recente para a mais antiga (SPEC-0021, FR-002)."""
    return list(
        session.scalars(
            select(ConversaAssistente)
            .where(
                ConversaAssistente.pessoa_id == identity.person_id,
                ConversaAssistente.tenant_id == identity.tenant_id,
                ConversaAssistente.project_id == identity.project_id,
            )
            .order_by(ConversaAssistente.atualizada_em.desc(), ConversaAssistente.criada_em.desc())
            .limit(limite)
        )
    )


def get_conversa_or_404(
    session: Session, conversa_id: str, identity: Identity
) -> ConversaAssistente:
    """Só a autora enxerga a conversa; qualquer outra pessoa recebe o mesmo 404."""
    conversa = session.get(ConversaAssistente, conversa_id)
    if (
        conversa is None
        or conversa.pessoa_id != identity.person_id
        or conversa.tenant_id != identity.tenant_id
        or conversa.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return conversa


def list_mensagens_recentes(
    session: Session, conversa_id: str, limite: int = _JANELA_DE_MENSAGENS
) -> list[MensagemAssistente]:
    """As ``limite`` mensagens mais recentes da conversa, em ordem cronológica."""
    recentes = session.scalars(
        select(MensagemAssistente)
        .where(MensagemAssistente.conversa_id == conversa_id)
        .order_by(MensagemAssistente.criada_em.desc())
        .limit(limite)
    )
    return list(reversed(list(recentes)))


# --- Conexões de ingestão (SPEC-0026) -------------------------------------


def get_conexao_or_404(
    session: Session, conexao_id: str, identity: Identity, *, for_update: bool = False
) -> Conexao:
    """Conexão do tenant e projeto da pessoa; outra equipe recebe 404."""
    stmt = select(Conexao).where(
        Conexao.id == conexao_id,
        Conexao.tenant_id == identity.tenant_id,
        Conexao.project_id == identity.project_id,
    )
    if for_update:
        stmt = stmt.with_for_update()
    conexao = session.execute(stmt).scalar_one_or_none()
    if conexao is None:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    return conexao


def list_conexoes_for_identity(session: Session, identity: Identity) -> list[Conexao]:
    return list(
        session.execute(
            select(Conexao)
            .where(
                Conexao.tenant_id == identity.tenant_id,
                Conexao.project_id == identity.project_id,
            )
            .order_by(func.lower(Conexao.nome), Conexao.id)
        )
        .scalars()
        .all()
    )


def contar_bases_da_conexao(session: Session, conexao_id: str) -> int:
    """Quantas Coleções e Bases legadas (não apagadas) usam a conexão.

    O nome é anterior à SPEC-0030; desde então a Coleção é a unidade de uso e a Base
    só aparece enquanto o comando de descarte não a apagou.
    """
    bases = session.execute(
        select(func.count())
        .select_from(Base)
        .where(
            Base.apagada_em.is_(None),
            (Base.conexao_embeddings_id == conexao_id)
            | (Base.conexao_vector_store_id == conexao_id),
        )
    ).scalar_one()
    colecoes = session.execute(
        select(func.count())
        .select_from(Colecao)
        .where(
            Colecao.apagada_em.is_(None),
            (Colecao.conexao_embeddings_id == conexao_id)
            | (Colecao.conexao_vector_store_id == conexao_id),
        )
    ).scalar_one()
    return int(bases) + int(colecoes)


def _garantir_nome_livre(
    session: Session, identity: Identity, nome: str, *, ignorar_id: str | None = None
) -> None:
    stmt = select(Conexao.id).where(
        Conexao.tenant_id == identity.tenant_id,
        Conexao.project_id == identity.project_id,
        func.lower(Conexao.nome) == nome.lower(),
    )
    if ignorar_id:
        stmt = stmt.where(Conexao.id != ignorar_id)
    if session.execute(stmt).first() is not None:
        raise HTTPException(status_code=409, detail="Já existe uma conexão com este nome.")


def _evento(session: Session, identity: Identity, conexao_id: str, acao: str) -> None:
    registrar_evento_conexao(
        session,
        acao,
        conexao_id=conexao_id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        ator_pessoa_id=identity.person_id,
    )


def criar_conexao(
    session: Session,
    identity: Identity,
    *,
    nome: str,
    tipo: str,
    configuracao: dict,
    segredo_cifrado: str | None,
) -> Conexao:
    """Cria a conexão e o evento `criada` na mesma transação (sem commit)."""
    _garantir_nome_livre(session, identity, nome)
    conexao = Conexao(
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        nome=nome,
        tipo=tipo,
        situacao="ativa",
        configuracao=configuracao,
        segredo_cifrado=segredo_cifrado,
        criado_por=identity.person_id,
    )
    session.add(conexao)
    session.flush()
    _evento(session, identity, conexao.id, "criada")
    return conexao


def atualizar_conexao(
    session: Session,
    identity: Identity,
    conexao: Conexao,
    *,
    nome: str | None = None,
    configuracao: dict | None = None,
    segredo_cifrado: str | None = None,
) -> Conexao:
    """Aplica a edição; `editada` para nome ou configuração, `chave_trocada` para a chave."""
    if nome is not None and nome != conexao.nome:
        _garantir_nome_livre(session, identity, nome, ignorar_id=conexao.id)
    editada = False
    if nome is not None and nome != conexao.nome:
        conexao.nome = nome
        editada = True
    if configuracao is not None and configuracao != conexao.configuracao:
        conexao.configuracao = configuracao
        editada = True
    if editada:
        _evento(session, identity, conexao.id, "editada")
    if segredo_cifrado is not None:
        conexao.segredo_cifrado = segredo_cifrado
        _evento(session, identity, conexao.id, "chave_trocada")
    session.flush()
    return conexao


def alterar_situacao_conexao(
    session: Session, identity: Identity, conexao: Conexao, situacao: str
) -> Conexao:
    """Desativa ou reativa; vínculos, histórico e vetores não são tocados."""
    if conexao.situacao != situacao:
        conexao.situacao = situacao
        _evento(
            session, identity, conexao.id, "desativada" if situacao == "desativada" else "reativada"
        )
        session.flush()
    return conexao


def excluir_conexao(session: Session, identity: Identity, conexao: Conexao) -> None:
    """Remove a conexão somente sem Base vinculada; com uso devolve 409."""
    em_uso = contar_bases_da_conexao(session, conexao.id)
    if em_uso:
        raise HTTPException(
            status_code=409,
            detail=f"A conexão está em uso por {em_uso} Coleção(ões) e não pode ser excluída.",
        )
    conexao_id = conexao.id
    # Registros apagados só guardam a chave estrangeira; sem filhos, saem junto.
    session.execute(
        delete(Colecao).where(
            Colecao.apagada_em.is_not(None),
            (Colecao.conexao_embeddings_id == conexao_id)
            | (Colecao.conexao_vector_store_id == conexao_id),
        )
    )
    session.execute(
        delete(Base).where(
            Base.apagada_em.is_not(None),
            (Base.conexao_embeddings_id == conexao_id)
            | (Base.conexao_vector_store_id == conexao_id),
        )
    )
    _evento(session, identity, conexao_id, "excluida")
    session.delete(conexao)
    session.flush()


def get_colecao_or_404(session: Session, colecao_id: str, identity: Identity) -> Colecao:
    colecao = session.get(Colecao, colecao_id)
    if (
        colecao is None
        or colecao.apagada_em is not None
        or colecao.tenant_id != identity.tenant_id
        or colecao.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Coleção não encontrada.")
    return colecao


def get_envio_or_404(session: Session, envio_id: str, identity: Identity) -> Envio:
    envio = session.get(Envio, envio_id)
    if envio is None:
        raise HTTPException(status_code=404, detail="Envio não encontrado.")
    try:
        get_colecao_or_404(session, envio.colecao_id, identity)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Envio não encontrado.") from None
    return envio


def has_active_colecoes_for_workspace(session: Session, workspace_id: str) -> bool:
    stmt = (
        select(Colecao.id)
        .where(Colecao.workspace_id == workspace_id, Colecao.apagada_em.is_(None))
        .limit(1)
    )
    return session.execute(stmt).first() is not None


def has_envio_ativo(session: Session, colecao_id: str) -> bool:
    stmt = select(Envio.id).where(
        Envio.colecao_id == colecao_id, Envio.situacao.in_(("queued", "running"))
    )
    return session.execute(stmt).first() is not None


def list_colecoes_for_workspace(
    session: Session, identity: Identity, workspace_id: str
) -> list[dict]:
    """Coleções ativas do Workspace com contagem de documentos, chunks e último envio."""
    colecoes = list(
        session.execute(
            select(Colecao)
            .where(
                Colecao.workspace_id == workspace_id,
                Colecao.tenant_id == identity.tenant_id,
                Colecao.project_id == identity.project_id,
                Colecao.apagada_em.is_(None),
            )
            .order_by(Colecao.criado_em.desc(), Colecao.id.desc())
        )
        .scalars()
        .all()
    )
    ids = [colecao.id for colecao in colecoes]
    totais = {
        colecao_id: (documentos, chunks or 0)
        for colecao_id, documentos, chunks in session.execute(
            select(
                DocumentoColecao.colecao_id,
                func.count(DocumentoColecao.id),
                func.sum(DocumentoColecao.chunks),
            )
            .where(DocumentoColecao.colecao_id.in_(ids))
            .group_by(DocumentoColecao.colecao_id)
        ).all()
    }
    ultimos = dict(
        session.execute(
            select(Envio.colecao_id, func.max(Envio.iniciado_em))
            .where(Envio.colecao_id.in_(ids))
            .group_by(Envio.colecao_id)
        ).all()
    )
    return [
        {
            "colecao": colecao,
            "documentos": totais.get(colecao.id, (0, 0))[0],
            "chunks": int(totais.get(colecao.id, (0, 0))[1]),
            "ultimo_envio_em": ultimos.get(colecao.id),
        }
        for colecao in colecoes
    ]


def list_documentos_da_colecao(session: Session, colecao_id: str) -> list[DocumentoColecao]:
    stmt = (
        select(DocumentoColecao)
        .options(selectinload(DocumentoColecao.ultimo_envio))
        .where(DocumentoColecao.colecao_id == colecao_id)
        .order_by(DocumentoColecao.nome_arquivo)
    )
    return list(session.execute(stmt).scalars().all())


def list_envios_da_colecao(session: Session, colecao_id: str) -> list[Envio]:
    stmt = (
        select(Envio)
        .options(selectinload(Envio.autor))
        .where(Envio.colecao_id == colecao_id)
        .order_by(Envio.iniciado_em.desc(), Envio.id.desc())
    )
    return list(session.execute(stmt).scalars().all())


def obter_conteudo(session: Session, documento_id: str) -> ConteudoDocumento | None:
    """Conteúdo processado da versão atual do documento (SPEC-0031)."""
    return session.execute(
        select(ConteudoDocumento).where(ConteudoDocumento.documento_id == documento_id)
    ).scalar_one_or_none()


def salvar_conteudo(
    session: Session,
    documento_id: str,
    *,
    texto: str,
    trechos: list[dict],
    envio_id: str,
    truncado: bool,
) -> ConteudoDocumento:
    """Grava ou substitui o conteúdo do documento: sempre uma única versão (FR-005)."""
    conteudo = obter_conteudo(session, documento_id)
    if conteudo is None:
        conteudo = ConteudoDocumento(documento_id=documento_id)
        session.add(conteudo)
    conteudo.texto = texto
    conteudo.trechos = trechos
    conteudo.envio_id = envio_id
    conteudo.truncado = truncado
    conteudo.atualizado_em = datetime.now(UTC)
    return conteudo


def apagar_conteudo_do_documento(session: Session, documento_id: str) -> None:
    session.execute(delete(ConteudoDocumento).where(ConteudoDocumento.documento_id == documento_id))


def apagar_conteudos_da_colecao(session: Session, colecao_id: str) -> None:
    """Remove o conteúdo dos documentos da coleção; precede a exclusão deles (chave estrangeira)."""
    ids = select(DocumentoColecao.id).where(DocumentoColecao.colecao_id == colecao_id)
    session.execute(delete(ConteudoDocumento).where(ConteudoDocumento.documento_id.in_(ids)))
