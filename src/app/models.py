"""Modelos ORM da aplicação (SPEC-0012, SPEC-0019, SPEC-0020, SPEC-0021 e SPEC-0026)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.app.db import ORMBase

__all__ = [
    "Base",
    "Colecao",
    "Conexao",
    "ConteudoDocumento",
    "ConversaAssistente",
    "DocumentoColecao",
    "DocumentoConversao",
    "DominioWorkspace",
    "Envio",
    "EventoAcesso",
    "EventoConexao",
    "ExclusaoLimpeza",
    "Execution",
    "LoteConversao",
    "MensagemAssistente",
    "Pessoa",
    "Query",
    "RelatorioLote",
    "Sessao",
    "TentativaLogin",
    "VinculoPessoa",
    "Workspace",
]


def _novo_id() -> str:
    return str(uuid.uuid4())


def _agora() -> datetime:
    return datetime.now(UTC)


class Pessoa(ORMBase):
    """Pessoa autenticável do produto; nunca é removida fisicamente."""

    __tablename__ = "pessoas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320))
    senha_hash: Mapped[str] = mapped_column(Text)
    precisa_trocar_senha: Mapped[bool] = mapped_column(Boolean, default=True)
    situacao: Mapped[str] = mapped_column(String(20), default="ativa")
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    criada_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora
    )

    __table_args__ = (Index("uq_pessoas_email_lower", func.lower(email), unique=True),)

    vinculo: Mapped[VinculoPessoa | None] = relationship(
        back_populates="pessoa", uselist=False, foreign_keys="VinculoPessoa.pessoa_id"
    )
    sessoes: Mapped[list[Sessao]] = relationship(
        back_populates="pessoa", cascade="all, delete-orphan"
    )


class VinculoPessoa(ORMBase):
    """Escopo único de tenant, projeto e papel de uma pessoa."""

    __tablename__ = "vinculos_pessoa"
    __table_args__ = (Index("ix_vinculos_pessoa_tenant_project", "tenant_id", "project_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    pessoa_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pessoas.id"), unique=True, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    papel: Mapped[str] = mapped_column(String(20))

    pessoa: Mapped[Pessoa] = relationship(back_populates="vinculo", foreign_keys=[pessoa_id])


class Sessao(ORMBase):
    """Sessão opaca; somente o resumo do token é persistido."""

    __tablename__ = "sessoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    pessoa_id: Mapped[str] = mapped_column(String(36), ForeignKey("pessoas.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    pessoa: Mapped[Pessoa] = relationship(back_populates="sessoes")


class TentativaLogin(ORMBase):
    """Contador por e-mail normalizado, exista ou não uma pessoa correspondente."""

    __tablename__ = "tentativas_login"

    email_normalizado: Mapped[str] = mapped_column(String(320), primary_key=True)
    falhas_seguidas: Mapped[int] = mapped_column(Integer, default=0)
    bloqueada_ate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora
    )


class EventoAcesso(ORMBase):
    """Evento de segurança sem credenciais, hashes ou tokens."""

    __tablename__ = "eventos_acesso"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tipo: Mapped[str] = mapped_column(String(50), index=True)
    motivo: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    ator_pessoa_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    alvo_pessoa_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    tenant_id: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    project_id: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, index=True)


class Conexao(ORMBase):
    """Conexão reutilizável de embeddings OpenAI ou Qdrant (SPEC-0026).

    A chave nunca é guardada em claro: ``segredo_cifrado`` recebe o texto
    Fernet produzido por ``src.app.conexoes``.
    """

    __tablename__ = "conexoes"
    __table_args__ = (Index("ix_conexoes_escopo_situacao", "tenant_id", "project_id", "situacao"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    nome: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(30))
    situacao: Mapped[str] = mapped_column(String(20), default="ativa")
    configuracao: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'::json")
    )
    segredo_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora
    )

    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class EventoConexao(ORMBase):
    """Histórico das alterações de uma conexão, sem valores nem segredos."""

    __tablename__ = "eventos_conexao"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    # Sem chave estrangeira: o evento sobrevive à exclusão da conexão.
    conexao_id: Mapped[str] = mapped_column(String(36), index=True)
    acao: Mapped[str] = mapped_column(String(30))
    ator_pessoa_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora, index=True)


class Workspace(ORMBase):
    """Agrupador de bases dentro de um tenant e projeto."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    nome: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )

    ia_externa_permitida: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    conexao_ia_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conexoes.id"), nullable=True, default=None
    )

    bases: Mapped[list[Base]] = relationship(back_populates="workspace")
    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class Base(ORMBase):
    """Uma base Markdown de um projeto/tenant (upload ou preparada)."""

    __tablename__ = "bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"))
    nome: Mapped[str] = mapped_column(String(255))
    origem: Mapped[str] = mapped_column(String(20))
    collection_name: Mapped[str] = mapped_column(String(255))
    metadados_chunk: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, default=list, server_default=text("'[]'::json")
    )
    documentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # SPEC-0026: nulos nas Bases anteriores, que seguem a configuração global.
    conexao_embeddings_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conexoes.id", ondelete="RESTRICT"), nullable=True, default=None
    )
    conexao_vector_store_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conexoes.id", ondelete="RESTRICT"), nullable=True, default=None
    )
    chunking: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )

    workspace: Mapped[Workspace] = relationship(back_populates="bases")
    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class Execution(ORMBase):
    """Uma execução do pipeline sobre uma base (situação, etapa, contagens).

    ``uq_executions_base_active`` garante no máximo uma execução
    ``pending``/``running`` por ``base_id`` (SPEC-0015, FR-001) — corrige a
    corrida entre ``has_active_execution`` e este insert, atomicamente, no
    banco.
    """

    __tablename__ = "executions"
    __table_args__ = (
        Index(
            "uq_executions_base_active",
            "base_id",
            unique=True,
            postgresql_where=text("situacao IN ('pending', 'running')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    base_id: Mapped[str] = mapped_column(String(36), ForeignKey("bases.id"))
    situacao: Mapped[str] = mapped_column(String(20))
    etapa: Mapped[str] = mapped_column(String(50), default="")
    previstos: Mapped[int] = mapped_column(Integer, default=0)
    inseridos: Mapped[int] = mapped_column(Integer, default=0)
    mantidos: Mapped[int] = mapped_column(Integer, default=0)
    removidos: Mapped[int] = mapped_column(Integer, default=0)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )

    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class Query(ORMBase):
    """Uma consulta de validação realizada sobre uma base indexada."""

    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    # SPEC-0030: a consulta passa a pertencer a uma coleção; `base_id` fica legado.
    base_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("bases.id"), nullable=True, default=None
    )
    colecao_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("colecoes.id"), nullable=True, default=None, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    pergunta: Mapped[str] = mapped_column(Text)
    resultado: Mapped[str] = mapped_column(Text, default="")
    chunks_fontes: Mapped[Any] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )

    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class Colecao(ORMBase):
    """Coleção de documentos de um Workspace (SPEC-0030).

    O nome exibido é editável; ``nome_fisico`` é a coleção no Qdrant, gerada na
    criação e imutável. Conexões e dimensão ficam fixas desde o primeiro envio.
    """

    __tablename__ = "colecoes"
    __table_args__ = (
        Index(
            "uq_colecoes_nome_ativo",
            "workspace_id",
            "nome_normalizado",
            unique=True,
            postgresql_where=text("apagada_em IS NULL"),
        ),
        Index(
            "uq_colecoes_nome_fisico_ativo",
            "conexao_vector_store_id",
            "nome_fisico",
            unique=True,
            postgresql_where=text("apagada_em IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    nome_normalizado: Mapped[str] = mapped_column(String(80))
    nome_fisico: Mapped[str] = mapped_column(String(255))
    conexao_embeddings_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conexoes.id", ondelete="RESTRICT")
    )
    conexao_vector_store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conexoes.id", ondelete="RESTRICT")
    )
    dimensao: Mapped[int] = mapped_column(Integer)
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    revisada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    revisada_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )

    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])
    workspace: Mapped[Workspace] = relationship()


class Envio(ORMBase):
    """Um envio de arquivos para uma coleção (situação, contagens e erro seguro)."""

    __tablename__ = "envios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    colecao_id: Mapped[str] = mapped_column(String(36), ForeignKey("colecoes.id"), index=True)
    arquivos: Mapped[list[str]] = mapped_column(JSON, default=list)
    processamento: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadados_chunk: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, default=list, server_default=text("'[]'::json")
    )
    situacao: Mapped[str] = mapped_column(String(20), default="queued")
    etapa: Mapped[str] = mapped_column(String(50), default="")
    previstos: Mapped[int] = mapped_column(Integer, default=0)
    inseridos: Mapped[int] = mapped_column(Integer, default=0)
    mantidos: Mapped[int] = mapped_column(Integer, default=0)
    removidos: Mapped[int] = mapped_column(Integer, default=0)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )

    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])


class DocumentoColecao(ORMBase):
    """Versão atual de um documento da coleção, identificado pelo nome do arquivo."""

    __tablename__ = "documentos_colecao"
    __table_args__ = (
        Index("uq_documentos_colecao_nome", "colecao_id", "nome_arquivo", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    colecao_id: Mapped[str] = mapped_column(String(36), ForeignKey("colecoes.id"), index=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    document_id: Mapped[str] = mapped_column(String(200))
    source_hash: Mapped[str] = mapped_column(String(64))
    chunks: Mapped[int] = mapped_column(Integer, default=0)
    chunking: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ultimo_envio_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("envios.id"), nullable=True, default=None
    )
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    ultimo_envio: Mapped[Envio | None] = relationship(foreign_keys=[ultimo_envio_id])


class ConteudoDocumento(ORMBase):
    """Conteúdo processado da versão atual de um documento (SPEC-0031).

    Uma linha por documento: o texto convertido (cortado em ``truncado`` quando passa do
    limite) e os trechos (``ordem`` a partir de 1, ``texto`` e ``etiquetas`` como
    dicionário rótulo → valor). Só existe para documento cuja sincronização o destino
    confirmou e some junto do documento.
    """

    __tablename__ = "conteudos_documento"
    __table_args__ = (Index("uq_conteudos_documento_documento", "documento_id", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    documento_id: Mapped[str] = mapped_column(String(36), ForeignKey("documentos_colecao.id"))
    texto: Mapped[str] = mapped_column(Text)
    trechos: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    envio_id: Mapped[str] = mapped_column(String(36), ForeignKey("envios.id"), index=True)
    truncado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class ConversaAssistente(ORMBase):
    """Conversa da pessoa com o assistente; visível somente à autora (SPEC-0021)."""

    __tablename__ = "conversas_assistente"
    __table_args__ = (
        Index("ix_conversas_assistente_pessoa_atualizada", "pessoa_id", "atualizada_em"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    pessoa_id: Mapped[str] = mapped_column(String(36), ForeignKey("pessoas.id"))
    titulo: Mapped[str] = mapped_column(String(60), default="Nova conversa")
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    atualizada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    mensagens: Mapped[list[MensagemAssistente]] = relationship(
        back_populates="conversa",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MensagemAssistente.criada_em",
    )


class MensagemAssistente(ORMBase):
    """Mensagem imutável de uma conversa; removida em cascata com ela."""

    __tablename__ = "mensagens_assistente"
    __table_args__ = (Index("ix_mensagens_assistente_conversa_criada", "conversa_id", "criada_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    conversa_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversas_assistente.id", ondelete="CASCADE")
    )
    papel: Mapped[str] = mapped_column(String(20))
    conteudo: Mapped[str] = mapped_column(Text)
    # Sem chave estrangeira: a mensagem sobrevive à exclusão lógica da Base.
    base_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    fontes: Mapped[list[str]] = mapped_column(JSON, default=list, server_default=text("'[]'::json"))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    conversa: Mapped[ConversaAssistente] = relationship(back_populates="mensagens")


class LoteConversao(ORMBase):
    """Um lote de documentos enviados para conversão em Markdown (SPEC-0023)."""

    __tablename__ = "lotes_conversao"
    __table_args__ = (Index("ix_lotes_conversao_workspace_criado", "workspace_id", "criado_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"))
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    situacao: Mapped[str] = mapped_column(String(30), default="processando")
    dominio_versao_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dominios_workspace.id"), nullable=True, default=None
    )

    workspace: Mapped[Workspace] = relationship(foreign_keys=[workspace_id])
    autor: Mapped[Pessoa | None] = relationship(foreign_keys=[criado_por])
    documentos: Mapped[list[DocumentoConversao]] = relationship(back_populates="lote")


class DocumentoConversao(ORMBase):
    """Um documento de um lote de conversão; sem relação com `Base` (SPEC-0023)."""

    __tablename__ = "documentos_conversao"
    __table_args__ = (Index("ix_documentos_conversao_lote", "lote_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    lote_id: Mapped[str] = mapped_column(String(36), ForeignKey("lotes_conversao.id"))
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    formato: Mapped[str] = mapped_column(String(20))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    origem_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    abas_disponiveis: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    abas_selecionadas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reprocessado_ia_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    avisos: Mapped[list[dict]] = mapped_column(JSON, default=list, server_default="[]")
    limpeza_situacao: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)
    duvidas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    exclusoes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    limpeza_erro: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    situacao: Mapped[str] = mapped_column(String(20), default="fila")
    erro: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    apagado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    grupo_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("grupos_imagem.id"), nullable=True, default=None, index=True
    )
    posicao_no_grupo: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    modificado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    pasta_origem: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)

    lote: Mapped[LoteConversao] = relationship(back_populates="documentos")


class GrupoImagem(ORMBase):
    """Grupo de imagens de um lote, proposto pelo sistema e aprovado pela pessoa (SPEC-0040)."""

    __tablename__ = "grupos_imagem"
    __table_args__ = (Index("ix_grupos_imagem_lote", "lote_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    lote_id: Mapped[str] = mapped_column(String(36), ForeignKey("lotes_conversao.id"))
    ordem: Mapped[int] = mapped_column(Integer)
    certeza: Mapped[str] = mapped_column(String(10), default="incerta")
    aprovado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    documento_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)


class DominioWorkspace(ORMBase):
    """Versão do resumo do domínio da empresa de um Workspace (SPEC-0037)."""

    __tablename__ = "dominios_workspace"
    __table_args__ = (
        UniqueConstraint("workspace_id", "versao", name="uq_dominios_workspace_versao"),
        Index("ix_dominios_workspace_vigente", "workspace_id", "vigente"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"))
    versao: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)
    vigente: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    aprovado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class ExclusaoLimpeza(ORMBase):
    """Uma remoção feita pela limpeza; o trecho some após 30 dias (SPEC-0037)."""

    __tablename__ = "exclusoes_limpeza"
    __table_args__ = (Index("ix_exclusoes_limpeza_lote", "lote_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    lote_id: Mapped[str] = mapped_column(String(36), ForeignKey("lotes_conversao.id"))
    documento_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("documentos_conversao.id"), nullable=True, default=None
    )
    arquivo: Mapped[str] = mapped_column(String(255))
    posicao: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(200))
    camada: Mapped[str] = mapped_column(String(20))
    confianca: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    trecho: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    mantido_em: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class RelatorioLote(ORMBase):
    """Relatório da limpeza de um lote, guardado por 90 dias (SPEC-0037)."""

    __tablename__ = "relatorios_lote"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    lote_id: Mapped[str] = mapped_column(String(36), ForeignKey("lotes_conversao.id"), unique=True)
    conteudo: Mapped[str] = mapped_column(Text)
    ia_usada: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    provedor: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    dominio_versao_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dominios_workspace.id"), nullable=True, default=None
    )
    contagens: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'::json")
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class AnaliseContradicao(ORMBase):
    """Uma análise de contradições de uma coleção; vence em 90 dias (SPEC-0038)."""

    __tablename__ = "analises_contradicao"
    __table_args__ = (Index("ix_analises_contradicao_colecao", "colecao_id", "criado_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    colecao_id: Mapped[str] = mapped_column(String(36), ForeignKey("colecoes.id"))
    situacao: Mapped[str] = mapped_column(String(20), default="em_andamento")
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    iniciada_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    provedor: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    dominio_versao_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dominios_workspace.id"), nullable=True, default=None
    )
    total_assuntos: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    concluidos: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    documentos_analisados: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    progresso: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, server_default=text("'{}'::json")
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class OcorrenciaContradicao(ORMBase):
    """Uma contradição achada numa análise, com os trechos de origem (SPEC-0038)."""

    __tablename__ = "ocorrencias_contradicao"
    __table_args__ = (
        Index("ix_ocorrencias_contradicao_analise", "analise_id"),
        UniqueConstraint(
            "analise_id",
            "assunto_normalizado",
            "chave_trechos",
            name="uq_ocorrencias_contradicao_idempotencia",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    analise_id: Mapped[str] = mapped_column(String(36), ForeignKey("analises_contradicao.id"))
    assunto: Mapped[str] = mapped_column(String(200))
    assunto_normalizado: Mapped[str] = mapped_column(String(200))
    etiqueta: Mapped[str] = mapped_column(String(30))
    impacto: Mapped[str] = mapped_column(String(10), default="baixo")
    chave_trechos: Mapped[str] = mapped_column(String(64))
    trechos: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    explicacao: Mapped[str] = mapped_column(Text, default="")
    arquivo_mais_antigo: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class RespostaEmpresa(ORMBase):
    """Resposta colada da empresa sobre as contradições de uma análise (SPEC-0039)."""

    __tablename__ = "respostas_empresa"
    __table_args__ = (Index("ix_respostas_empresa_colecao", "colecao_id", "criado_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    colecao_id: Mapped[str] = mapped_column(String(36), ForeignKey("colecoes.id"))
    analise_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("analises_contradicao.id", ondelete="SET NULL"), nullable=True
    )
    texto: Mapped[str] = mapped_column(Text)
    situacao: Mapped[str] = mapped_column(String(20), default="concluida")
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    criado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class PropostaCorrecao(ORMBase):
    """Proposta de correção para uma contradição; só vira escrita após confirmação."""

    __tablename__ = "propostas_correcao"
    __table_args__ = (Index("ix_propostas_correcao_resposta", "resposta_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    resposta_id: Mapped[str] = mapped_column(String(36), ForeignKey("respostas_empresa.id"))
    ocorrencia_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("ocorrencias_contradicao.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    situacao: Mapped[str] = mapped_column(String(20))
    arquivo: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    documento_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    trecho_alvo: Mapped[str] = mapped_column(Text, default="")
    texto_corrigido: Mapped[str] = mapped_column(Text, default="")
    hash_documento: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    motivo: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)


class DecisaoEmpresa(ORMBase):
    """Registro de uma correção confirmada ou de uma volta de versão (SPEC-0039)."""

    __tablename__ = "decisoes_empresa"
    __table_args__ = (Index("ix_decisoes_empresa_colecao", "colecao_id", "confirmado_em"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    proposta_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("propostas_correcao.id"), nullable=True, default=None
    )
    colecao_id: Mapped[str] = mapped_column(String(36), ForeignKey("colecoes.id"))
    ocorrencia_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    arquivo: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    confirmado_por: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pessoas.id"), nullable=True, default=None
    )
    confirmado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    editada: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    versao_resultante: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    restaurada_de: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    resposta_trecho: Mapped[str] = mapped_column(Text, default="")
    texto_proposto: Mapped[str] = mapped_column(Text, default="")
    texto_aplicado: Mapped[str] = mapped_column(Text, default="")


class VersaoDocumento(ORMBase):
    """Versão numerada de um documento da coleção; as não atuais vencem em 90 dias."""

    __tablename__ = "versoes_documento"
    __table_args__ = (Index("uq_versoes_documento_numero", "documento_id", "numero", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    documento_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documentos_colecao.id", ondelete="CASCADE")
    )
    numero: Mapped[int] = mapped_column(Integer)
    chave_armazenamento: Mapped[str] = mapped_column(String(255))
    hash: Mapped[str] = mapped_column(String(64))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class RegistroExclusaoDecisoes(ORMBase):
    """Registro mínimo que resta quando a coleção é apagada, sem texto da empresa."""

    __tablename__ = "registros_exclusao_decisoes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    colecao_id: Mapped[str] = mapped_column(String(36))
    apagado_por: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    apagado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    decisoes: Mapped[int] = mapped_column(Integer, default=0)
