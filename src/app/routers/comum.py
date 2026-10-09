"""Helpers compartilhados pelos routers de envio e de coleção (SPEC-0030)."""

from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.app import repo
from src.app.auth import Identity
from src.app.models import Workspace

__all__ = ["autor_json", "metadados_do_upload", "workspace_do_upload"]


def autor_json(registro) -> dict | None:
    if registro.autor is None:
        return None
    return {
        "id": registro.autor.id,
        "nome": registro.autor.nome,
        "desativada": registro.autor.situacao != "ativa",
    }


def workspace_do_upload(
    session: Session, workspace_id: str | None, identity: Identity
) -> Workspace:
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Informe o Workspace do envio.")
    try:
        return repo.get_workspace_or_404(session, workspace_id, identity)
    except HTTPException as erro:
        if erro.status_code != 404:
            raise
        raise HTTPException(
            status_code=400, detail="Workspace inválido para este projeto."
        ) from None


def metadados_do_upload(valor: str | None) -> list[dict[str, str]]:
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
