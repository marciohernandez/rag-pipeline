"""Endpoints de bases: upload, base preparada e exclusão (SPEC-0012, US-001/US-002)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.app import repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Base, Execution, Query, Workspace
from src.app.settings import get_settings
from src.app.storage import get_storage
from src.app.tasks import scope_project_id

router = APIRouter(prefix="/api/v1", tags=["bases"])

MAX_ARQUIVOS = 50
MAX_BYTES_POR_ARQUIVO = 5 * 1024 * 1024
MAX_BYTES_TOTAL = 50 * 1024 * 1024
BASE_PREPARADA_DIR = Path("documentos/base_exemplo")


def _agora() -> datetime:
    return datetime.now(UTC)


def _serializar_execucao(execucao: Execution) -> dict:
    return {
        "id": execucao.id,
        "situacao": execucao.situacao,
        "etapa": execucao.etapa,
        "previstos": execucao.previstos,
        "inseridos": execucao.inseridos,
        "mantidos": execucao.mantidos,
        "removidos": execucao.removidos,
        "erro": execucao.erro,
        "iniciado_em": execucao.iniciado_em.isoformat(),
        "concluido_em": (
            execucao.concluido_em.isoformat() if execucao.concluido_em is not None else None
        ),
        "criado_por": _autor(execucao),
    }


def _autor(registro) -> dict | None:
    if registro.autor is None:
        return None
    return {
        "id": registro.autor.id,
        "nome": registro.autor.nome,
        "desativada": registro.autor.situacao != "ativa",
    }


def _ler_base_preparada() -> list[tuple[str, bytes]]:
    return [
        (arquivo.name, arquivo.read_bytes())
        for arquivo in sorted(BASE_PREPARADA_DIR.glob("*.md"))
    ]


def _workspace_do_upload(
    session: Session, workspace_id: str | None, identity: Identity
) -> Workspace:
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Informe o Workspace da Base.")
    try:
        return repo.get_workspace_or_404(session, workspace_id, identity)
    except HTTPException as erro:
        if erro.status_code != 404:
            raise
        raise HTTPException(
            status_code=400, detail="Workspace inválido para este projeto."
        ) from None


def _metadados_do_upload(valor: str | None) -> list[dict[str, str]]:
    if valor is None or not valor.strip():
        return []
    try:
        dados = json.loads(valor)
    except json.JSONDecodeError as erro:
        raise HTTPException(status_code=400, detail="Metadados devem ser um JSON válido.") from erro
    if not isinstance(dados, list):
        raise HTTPException(status_code=400, detail="Metadados devem ser uma lista de pares.")

    resultado: list[dict[str, str]] = []
    rotulos: set[str] = set()
    for item in dados:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Cada metadado deve ter rótulo e valor.")
        rotulo = item.get("rotulo")
        conteudo = item.get("valor")
        if not isinstance(rotulo, str) or not rotulo.strip() or not isinstance(conteudo, str):
            raise HTTPException(status_code=400, detail="Cada metadado deve ter rótulo e valor.")
        rotulo = rotulo.strip()
        if rotulo in rotulos:
            raise HTTPException(status_code=400, detail=f"Rótulo de metadado repetido: {rotulo}.")
        rotulos.add(rotulo)
        resultado.append({"rotulo": rotulo, "valor": conteudo})
    return resultado


@router.get("/bases")
def listar_bases(
    workspace_id: str | None = None,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    """Lista as bases ativas do tenant/projeto do token (leitura livre, US-002)."""
    with SessionLocal() as session:
        if workspace_id is not None:
            repo.get_workspace_or_404(session, workspace_id, identity)
        pares = repo.list_bases_for_identity(session, identity, workspace_id)
        return [
            {
                "id": base.id,
                "nome": base.nome,
                "origem": base.origem,
                "workspace_id": base.workspace_id,
                "collection_name": base.collection_name,
                "metadados_chunk": base.metadados_chunk,
                "status": ultima.situacao if ultima is not None else "sem_execucao",
                "documentos": base.documentos,
                "chunks": (ultima.inseridos + ultima.mantidos) if ultima is not None else 0,
                "ultima_atualizacao": (
                    ultima.iniciado_em if ultima is not None else base.criado_em
                ).isoformat(),
                "criado_por": _autor(base),
            }
            for base, ultima in pares
        ]


@router.get("/bases/{base_id}")
def obter_base(base_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    """Detalhe de uma base com o histórico de execuções, da mais recente à mais antiga."""
    with SessionLocal() as session:
        base = repo.get_base_or_404(session, base_id, identity)
        execucoes = repo.list_executions_for_base(session, base.id)
        return {
            "id": base.id,
            "nome": base.nome,
            "origem": base.origem,
            "workspace_id": base.workspace_id,
            "collection_name": base.collection_name,
            "metadados_chunk": base.metadados_chunk,
            "documentos": base.documentos,
            "criado_em": base.criado_em.isoformat(),
            "criado_por": _autor(base),
            "execucoes": [_serializar_execucao(execucao) for execucao in execucoes],
        }


@router.post("/bases", status_code=201)
async def enviar_base(
    arquivos: list[UploadFile] | None = None,
    usar_base_preparada: bool = Form(False),
    workspace_id: str | None = Form(None),
    collection_name: str | None = Form(None),
    metadados_chunk: str | None = Form(None),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    arquivos = arquivos or []

    with SessionLocal() as session:
        workspace = _workspace_do_upload(session, workspace_id, identity)
        workspace_id_validado = workspace.id
    colecao = (collection_name or "").strip() or f"ws-{workspace_id_validado}"
    metadados = _metadados_do_upload(metadados_chunk)

    if usar_base_preparada:
        conteudos = _ler_base_preparada()
        nome_base = "base-preparada"
        origem = "preparada"
    else:
        if not arquivos:
            raise HTTPException(
                status_code=400, detail="Envie ao menos um arquivo .md ou use a base preparada."
            )
        if len(arquivos) > MAX_ARQUIVOS:
            raise HTTPException(
                status_code=400, detail=f"Limite de {MAX_ARQUIVOS} arquivos excedido."
            )

        conteudos = []
        total = 0
        for arquivo in arquivos:
            dados = await arquivo.read()
            # Path.name descarta qualquer diretório embutido no filename
            # (ex.: "../../tmp/evil.md" ou "sub/dir.md") antes de qualquer
            # uso — sem isso, storage.save monta o caminho final por
            # concatenação direta e escreveria fora do diretório da base.
            nome = Path(arquivo.filename or "").name
            if not nome or not nome.endswith(".md"):
                raise HTTPException(status_code=400, detail=f"Extensão inválida: {nome}.")
            if len(dados) > MAX_BYTES_POR_ARQUIVO:
                raise HTTPException(
                    status_code=400, detail=f"Arquivo {nome} excede o limite de 5 MB."
                )
            try:
                dados.decode("utf-8")
            except UnicodeDecodeError as erro:
                raise HTTPException(
                    status_code=400, detail=f"Arquivo {nome} não é UTF-8 válido."
                ) from erro
            total += len(dados)
            if total > MAX_BYTES_TOTAL:
                raise HTTPException(status_code=400, detail="Limite de 50 MB por envio excedido.")
            conteudos.append((nome, dados))

        nome_base = conteudos[0][0] if len(conteudos) == 1 else f"upload-{len(conteudos)}-arquivos"
        origem = "upload"

    base_id = str(uuid.uuid4())
    storage = get_storage()
    try:
        for nome, dados in conteudos:
            storage.save(base_id, nome, dados)
    except Exception:
        storage.delete_base(base_id)
        raise

    try:
        with SessionLocal() as session:
            base = Base(
                id=base_id,
                tenant_id=identity.tenant_id,
                project_id=identity.project_id,
                workspace_id=workspace_id_validado,
                nome=nome_base,
                origem=origem,
                collection_name=colecao,
                metadados_chunk=metadados,
                documentos=len(conteudos),
                criado_por=identity.person_id,
            )
            session.add(base)
            session.commit()
    except Exception:
        storage.delete_base(base_id)
        raise

    return {
        "base_id": base_id,
        "workspace_id": workspace_id_validado,
        "collection_name": colecao,
        "metadados_chunk": metadados,
    }


@router.delete("/bases/{base_id}", status_code=204)
def apagar_base(base_id: str, identity: Identity = Depends(get_identity)) -> None:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_base_or_404(session, base_id, identity)

    # Storage e vector store são apagados antes de qualquer escrita no
    # Postgres: se um dos dois falhar aqui, a exceção propaga sem ter
    # commitado o soft-delete, então a base continua visível/ativa e a
    # pessoa pode simplesmente repetir este DELETE (os dois passos abaixo já
    # são idempotentes — SPEC-0018).
    get_storage().delete_base(base_id)

    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    settings = get_settings()
    config = {
        "projeto": {"nome": scope_project_id(identity.tenant_id, identity.project_id, base_id)},
        "embedding": dict(settings.embedding),
        "vector_store": dict(settings.vector_store),
    }
    # tenant_id não é passado aqui: o caminho de escrita (src/pipeline/,
    # fora de escopo desta spec) nunca grava tenant_id no metadata do chunk,
    # então o escopo de escrita sempre tem tenant_id=None. O isolamento por
    # tenant já está garantido pela string composta acima; passar
    # tenant_id=identity.tenant_id aqui faria este LogicalScope nunca bater
    # com o da escrita (ver scope_project_id).
    service.delete_scope(config)

    with SessionLocal() as session:
        base = repo.get_base_or_404(session, base_id, identity)
        session.execute(delete(Execution).where(Execution.base_id == base.id))
        session.execute(delete(Query).where(Query.base_id == base.id))
        base.apagada_em = _agora()
        base.nome = ""
        session.commit()
