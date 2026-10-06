"""Repositório de conexões e retenção de eventos (SPEC-0026, T023)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from src.app import repo
from src.app.auth import Identity
from src.app.events import purgar_eventos_conexao
from src.app.models import Base, EventoConexao, Workspace
from tests._pessoas import criar_pessoa, sessao_do_banco


def _identidade(tenant: str = "tenant-1", projeto: str = "projeto-1") -> Identity:
    pessoa = criar_pessoa(papel="owner", tenant=tenant, projeto=projeto)
    return Identity(
        person_id=pessoa["id"],
        nome="Pessoa",
        email=pessoa["email"],
        tenant_id=tenant,
        project_id=projeto,
        role="owner",
        precisa_trocar_senha=False,
        session_id="s-1",
    )


def _criar(sessao, identidade, nome="Qdrant"):
    return repo.criar_conexao(
        sessao,
        identidade,
        nome=nome,
        tipo="qdrant",
        configuracao={"url": "https://q.exemplo.com"},
        segredo_cifrado="cifrado",
    )


def _acoes(sessao, conexao_id):
    linhas = sessao.execute(
        select(EventoConexao.acao).where(EventoConexao.conexao_id == conexao_id)
    ).scalars()
    return sorted(linhas)


def test_ciclo_de_vida_registra_um_evento_por_acao_sem_valores() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-004 AC-005"""
    identidade = _identidade()
    with sessao_do_banco() as sessao:
        conexao = _criar(sessao, identidade)
        repo.atualizar_conexao(sessao, identidade, conexao, nome="Qdrant produção")
        repo.atualizar_conexao(sessao, identidade, conexao, segredo_cifrado="outro")
        repo.alterar_situacao_conexao(sessao, identidade, conexao, "desativada")
        repo.alterar_situacao_conexao(sessao, identidade, conexao, "desativada")
        repo.alterar_situacao_conexao(sessao, identidade, conexao, "ativa")
        conexao_id = conexao.id
        sessao.commit()

        assert _acoes(sessao, conexao_id) == [
            "chave_trocada",
            "criada",
            "desativada",
            "editada",
            "reativada",
        ]
        repo.excluir_conexao(
            sessao, identidade, repo.get_conexao_or_404(sessao, conexao_id, identidade)
        )
        sessao.commit()
        assert "excluida" in _acoes(sessao, conexao_id)


def test_nome_duplicado_na_equipe_e_recusado_e_outra_equipe_nao_enxerga() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-005 AC-006"""
    dono, outra = _identidade(), _identidade("tenant-2", "projeto-2")
    with sessao_do_banco() as sessao:
        conexao = _criar(sessao, dono, "Principal")
        sessao.commit()
        with pytest.raises(HTTPException) as erro:
            _criar(sessao, dono, "principal")
        assert erro.value.status_code == 409
        with pytest.raises(HTTPException) as nao_achada:
            repo.get_conexao_or_404(sessao, conexao.id, outra)
        assert nao_achada.value.status_code == 404
        assert repo.list_conexoes_for_identity(sessao, outra) == []


def test_exclusao_com_base_vinculada_e_recusada_e_a_contagem_ignora_bases_apagadas() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-004 AC-005"""
    identidade = _identidade()
    with sessao_do_banco() as sessao:
        embeddings = repo.criar_conexao(
            sessao,
            identidade,
            nome="E",
            tipo="embeddings_openai",
            configuracao={"modelo": "m", "dimensoes": 8},
            segredo_cifrado="c",
        )
        qdrant = _criar(sessao, identidade)
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="WS")
        sessao.add(workspace)
        sessao.flush()
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            nome="b",
            origem="upload",
            collection_name="c",
            documentos=1,
            conexao_embeddings_id=embeddings.id,
            conexao_vector_store_id=qdrant.id,
        )
        sessao.add(base)
        sessao.commit()

        assert repo.contar_bases_da_conexao(sessao, embeddings.id) == 1
        with pytest.raises(HTTPException) as erro:
            repo.excluir_conexao(sessao, identidade, embeddings)
        assert erro.value.status_code == 409 and "1" in erro.value.detail
        base.apagada_em = datetime.now(UTC)
        sessao.commit()
        assert repo.contar_bases_da_conexao(sessao, embeddings.id) == 0


def test_purga_remove_somente_eventos_de_conexao_com_mais_de_90_dias() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-004 AC-006"""
    identidade = _identidade()
    agora = datetime.now(UTC)
    with sessao_do_banco() as sessao:
        for dias in (10, 89, 91, 200):
            sessao.add(
                EventoConexao(
                    tenant_id="tenant-1",
                    project_id="projeto-1",
                    conexao_id=f"c-{dias}",
                    acao="criada",
                    ator_pessoa_id=identidade.person_id,
                    criado_em=agora - timedelta(days=dias),
                )
            )
        sessao.commit()

        removidos = purgar_eventos_conexao(sessao, agora)

        restantes = sorted(sessao.execute(select(EventoConexao.conexao_id)).scalars())
        assert removidos == 2
        assert restantes == ["c-10", "c-89"]
