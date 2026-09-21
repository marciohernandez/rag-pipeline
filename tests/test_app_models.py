"""Contratos estruturais dos modelos persistentes da aplicação."""

from sqlalchemy.sql.schema import ForeignKey

from src.app.models import Base, Workspace


def test_workspace_declara_ownership_e_exclusao_logica() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-001 FR-002 AC-001 AC-002 AC-004."""
    tabela = Workspace.__table__

    assert tabela.name == "workspaces"
    assert set(tabela.columns) >= {
        tabela.c.id,
        tabela.c.tenant_id,
        tabela.c.project_id,
        tabela.c.nome,
        tabela.c.criado_em,
        tabela.c.apagada_em,
    }
    assert tabela.c.id.primary_key
    assert not tabela.c.tenant_id.nullable
    assert not tabela.c.project_id.nullable
    assert not tabela.c.nome.nullable
    assert tabela.c.apagada_em.nullable


def test_base_pertence_a_workspace_e_guarda_configuracao_de_ingestao() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-004 FR-005 FR-007 AC-004."""
    tabela = Base.__table__

    assert not tabela.c.workspace_id.nullable
    assert not tabela.c.collection_name.nullable
    assert not tabela.c.metadados_chunk.nullable
    assert tabela.c.metadados_chunk.default is not None
    assert callable(tabela.c.metadados_chunk.default.arg)
    assert str(tabela.c.metadados_chunk.server_default.arg) == "'[]'::json"

    chaves = list(tabela.c.workspace_id.foreign_keys)
    assert len(chaves) == 1
    assert isinstance(chaves[0], ForeignKey)
    assert chaves[0].target_fullname == "workspaces.id"
    assert Base.__mapper__.relationships["workspace"].back_populates == "bases"
    assert Workspace.__mapper__.relationships["bases"].back_populates == "workspace"
