"""Endpoint de consulta à base indexada (SPEC-0012, US-004)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app import repo
from src.app.auth import Identity, get_identity
from src.app.db import SessionLocal
from src.app.models import Execution, Query
from src.app.settings import get_settings
from src.app.tasks import scope_project_id

router = APIRouter(prefix="/api/v1", tags=["consultas"])


class ConsultaRequest(BaseModel):
    pergunta: str


@router.post("/bases/{base_id}/query")
def consultar_base(
    base_id: str, corpo: ConsultaRequest, identity: Identity = Depends(get_identity)  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        base = repo.get_base_or_404(session, base_id, identity)
        execucao_ok = (
            session.query(Execution)
            .filter_by(base_id=base.id, situacao="succeeded")
            .first()
        )
        if execucao_ok is None:
            raise HTTPException(
                status_code=409,
                detail="Esta base ainda não tem uma execução concluída com sucesso.",
            )

        settings = get_settings()
        config = {
            "projeto": {"nome": scope_project_id(identity.project_id, base.id)},
            "caminhos": {},
            "embedding": dict(settings.embedding),
            "vector_store": dict(settings.vector_store),
        }

        import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

        try:
            resultados = service.query_base(config, corpo.pergunta, tenant_id=identity.tenant_id)
        except Exception as erro:
            # Nunca repassar o detalhe do provedor ao cliente (NFR-002).
            raise HTTPException(
                status_code=502, detail="Não foi possível consultar a base indexada no momento."
            ) from erro

        resultados = list(resultados or [])
        melhor = resultados[0] if resultados else None
        chunks_fontes = [
            {
                "documento": resultado.metadata.get("nome_arquivo")
                or resultado.metadata.get("document_id"),
                "trecho": resultado.content,
            }
            for resultado in resultados
        ]
        resposta = {"resultado": melhor.content if melhor else "", "chunks_fontes": chunks_fontes}

        session.add(
            Query(
                base_id=base.id,
                tenant_id=identity.tenant_id,
                project_id=identity.project_id,
                pergunta=corpo.pergunta,
                resultado=resposta["resultado"],
                chunks_fontes=chunks_fontes,
            )
        )
        session.commit()
        return resposta
