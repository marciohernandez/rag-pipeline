"""Testes do enriquecimento de chunks na fronteira da aplicação."""

from langchain_core.documents import Document

from src.app.tasks import _mesclar_metadados_chunk


def test_limpeza_de_acesso_esta_registrada_como_tarefa_periodica_diaria() -> None:
    """SPECSFY: SPEC-0020 US-006 FR-012 NFR-004 AC-019."""
    from src.app import tasks

    registro = tasks.app.periodic_registry.periodic_tasks[
        ("purgar_dados_de_acesso_task", "")
    ]

    assert registro.task is tasks.purgar_dados_de_acesso_task
    assert registro.cron == "0 3 * * *"


def test_spec_0019_mescla_metadados_customizados_sem_sobrescrever_estrutura() -> None:
    """SPECSFY: SPEC-0019 US-003 FR-007 AC-014 AC-016."""
    chunk = Document(
        page_content="Conteúdo",
        metadata={"document_id": "doc-1", "project_id": "projeto-estrutural"},
    )

    resultado = _mesclar_metadados_chunk(
        [chunk],
        [
            {"rotulo": "canal", "valor": "fibra"},
            {"rotulo": "document_id", "valor": "não-substituir"},
        ],
    )

    assert resultado == [chunk]
    assert chunk.metadata == {
        "canal": "fibra",
        "document_id": "doc-1",
        "project_id": "projeto-estrutural",
    }


def test_spec_0019_lista_vazia_preserva_metadata_do_chunk() -> None:
    """SPECSFY: SPEC-0019 US-003 FR-007 AC-015."""
    chunk = Document(page_content="Conteúdo", metadata={"chunk_id": "chunk-1"})

    resultado = _mesclar_metadados_chunk([chunk], [])

    assert resultado == [chunk]
    assert chunk.metadata == {"chunk_id": "chunk-1"}
