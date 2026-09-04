from langchain_core.documents import Document

from src.pipeline.chunker import chunk_documents


def _config(min_children: int = 3) -> dict:
    return {
        "default_splitter": "header",
        "default_chunk_size": 1_000,
        "default_chunk_overlap": 0,
        "headers_to_split_on": [["#", "titulo"], ["##", "secao"], ["###", "subsecao"]],
        "generate_section_summaries": True,
        "section_summary_min_children": min_children,
    }


def _document(subsections: list[str]) -> Document:
    content = "# Catálogo\n\n## Planos\n\n" + "\n\n".join(
        f"### {title}\n\nDescrição de {title}." for title in subsections
    )
    return Document(
        page_content=content,
        metadata={
            "nome_arquivo": "catalogo.md",
            "caminho_relativo": "base/catalogo.md",
        },
    )


def test_generates_summary_with_ordered_unique_subsections() -> None:
    chunks = chunk_documents(
        [_document(["500 MEGA", "600 MEGA", "1 GIGA"])], _config(), project_id="base"
    )

    summaries = [chunk for chunk in chunks if chunk.metadata["chunk_type"] == "section_summary"]

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.metadata["summary_child_count"] == 3
    assert summary.metadata["secao"] == "Planos"
    assert summary.metadata["breadcrumb"] == "[Catálogo > Planos]"
    assert summary.page_content.endswith("- 500 MEGA\n- 600 MEGA\n- 1 GIGA")
    assert all(chunk.metadata["chunk_id"] for chunk in chunks)
    assert len({chunk.metadata["chunk_id"] for chunk in chunks}) == len(chunks)


def test_does_not_generate_summary_below_minimum() -> None:
    chunks = chunk_documents(
        [_document(["500 MEGA", "600 MEGA"])], _config(), project_id="base"
    )

    assert not [chunk for chunk in chunks if chunk.metadata["chunk_type"] == "section_summary"]


def test_identical_input_generates_identical_chunk_ids() -> None:
    first = chunk_documents(
        [_document(["500 MEGA", "600 MEGA", "1 GIGA"])], _config(), project_id="base"
    )
    second = chunk_documents(
        [_document(["500 MEGA", "600 MEGA", "1 GIGA"])], _config(), project_id="base"
    )

    assert [chunk.metadata["chunk_id"] for chunk in first] == [
        chunk.metadata["chunk_id"] for chunk in second
    ]


# SPECSFY: US-001 FR-001 FR-002 AC-001
def test_document_id_from_frontmatter_takes_precedence_over_generated_identity() -> None:
    document = Document(
        page_content="# Catálogo\n\n## Planos\n\nDescrição.",
        metadata={
            "nome_arquivo": "catalogo.md",
            "caminho_relativo": "base/catalogo.md",
            "document_id": "doc-rag-pipeline-42",
        },
    )

    chunks = chunk_documents([document], _config(), project_id="base")

    assert document.metadata["document_id"] == "doc-rag-pipeline-42"
    assert chunks
    assert all(chunk.metadata["document_id"] == "doc-rag-pipeline-42" for chunk in chunks)


# SPECSFY: US-001 FR-001 FR-002 NFR-002 AC-002
def test_document_id_absent_preserves_deterministic_generation() -> None:
    from src.pipeline.identity import stable_uuid

    document = _document(["500 MEGA", "600 MEGA", "1 GIGA"])

    chunks = chunk_documents([document], _config(), project_id="base")

    esperado = stable_uuid("document", "base", document.metadata["caminho_relativo"])
    assert document.metadata["document_id"] == esperado
    assert all(chunk.metadata["chunk_id"] for chunk in chunks)


# SPECSFY: US-001 FR-001 FR-002 AC-003
def test_changing_document_id_source_forces_consistent_new_chunk_ids() -> None:
    sem_id = _document(["500 MEGA", "600 MEGA", "1 GIGA"])
    chunks_sem_id = chunk_documents([sem_id], _config(), project_id="base")
    ids_sem_id = {chunk.metadata["chunk_id"] for chunk in chunks_sem_id}

    def _com_id() -> Document:
        documento = _document(["500 MEGA", "600 MEGA", "1 GIGA"])
        documento.metadata["document_id"] = "doc-rag-pipeline-99"
        return documento

    chunks_com_id_1 = chunk_documents([_com_id()], _config(), project_id="base")
    chunks_com_id_2 = chunk_documents([_com_id()], _config(), project_id="base")
    ids_com_id_1 = {chunk.metadata["chunk_id"] for chunk in chunks_com_id_1}
    ids_com_id_2 = {chunk.metadata["chunk_id"] for chunk in chunks_com_id_2}

    assert ids_com_id_1 != ids_sem_id
    assert ids_com_id_1 == ids_com_id_2


def _documento_qa(conteudo: str) -> Document:
    return Document(
        page_content=conteudo,
        metadata={
            "nome_arquivo": "qa.md",
            "caminho_relativo": "base/qa.md",
            "splitter": "qa",
        },
    )


# SPECSFY: US-004 FR-006 AC-012
def test_qa_splitter_creates_one_chunk_per_block() -> None:
    document = _documento_qa(
        "P: Um?\nR: Um.\n\n++++\n\nP: Dois?\nR: Dois.\n\n++++\n\nP: Três?\nR: Três."
    )

    chunks = chunk_documents([document], _config(), project_id="base")

    assert len(chunks) == 3
    assert "Um?" in chunks[0].page_content
    assert "Dois?" in chunks[1].page_content
    assert "Três?" in chunks[2].page_content


# SPECSFY: US-004 FR-006 AC-013
def test_qa_document_starting_with_separator_keeps_all_blocks() -> None:
    document = _documento_qa("++++\n\nP: Um?\nR: Um.\n\n++++\n\nP: Dois?\nR: Dois.")

    chunks = chunk_documents([document], _config(), project_id="base")

    assert len(chunks) == 2
    conteudo = " ".join(chunk.page_content for chunk in chunks)
    assert "Um?" in conteudo
    assert "Dois?" in conteudo


# SPECSFY: US-004 FR-006 AC-019
def test_qa_block_larger_than_chunk_size_stays_whole() -> None:
    resposta_longa = "R: " + ("palavra " * 300)
    document = _documento_qa(
        f"P: Pergunta longa?\n{resposta_longa}\n\n++++\n\nP: Curta?\nR: Sim."
    )

    chunks = chunk_documents([document], _config(), project_id="base")

    assert len(chunks) == 2
    assert "Pergunta longa" in chunks[0].page_content
    assert "palavra" in chunks[0].page_content


# SPECSFY: US-004 FR-007 NFR-002 AC-014
def test_document_without_qa_splitter_unaffected_by_separator_in_body() -> None:
    document = Document(
        page_content="# Título\n\nConteúdo com ++++ dentro do texto e outro --- também.",
        metadata={"nome_arquivo": "comum.md", "caminho_relativo": "base/comum.md"},
    )

    chunks = chunk_documents([document], _config(), project_id="base")

    assert len(chunks) == 1
    assert "++++" in chunks[0].page_content
    assert "---" in chunks[0].page_content


# SPECSFY: US-004 FR-007 AC-021
def test_multiple_separators_without_qa_splitter_do_not_trigger_qa_logic() -> None:
    document = Document(
        page_content="Texto\n\n++++\n\nMais texto\n\n++++\n\nAinda mais texto.",
        metadata={"nome_arquivo": "comum.md", "caminho_relativo": "base/comum.md"},
    )

    chunks = chunk_documents([document], _config(), project_id="base")

    assert len(chunks) == 1
    assert chunks[0].page_content.count("++++") == 2


# SPECSFY: US-005 FR-008 AC-015
def test_type_and_version_appear_in_every_chunk_without_affecting_identity() -> None:
    doc_com = _document(["500 MEGA"])
    doc_com.metadata["type"] = "faq"
    doc_com.metadata["version"] = "3"
    chunks_com = chunk_documents([doc_com], _config(), project_id="base")

    doc_sem = _document(["500 MEGA"])
    chunks_sem = chunk_documents([doc_sem], _config(), project_id="base")

    assert chunks_com
    assert all(chunk.metadata.get("type") == "faq" for chunk in chunks_com)
    assert all(chunk.metadata.get("version") == "3" for chunk in chunks_com)
    assert [chunk.metadata["chunk_id"] for chunk in chunks_com] == [
        chunk.metadata["chunk_id"] for chunk in chunks_sem
    ]


# SPECSFY: US-005 FR-008 NFR-002 AC-016
def test_missing_type_and_version_does_not_appear_in_chunks() -> None:
    document = _document(["500 MEGA"])

    chunks = chunk_documents([document], _config(), project_id="base")

    assert chunks
    assert all("type" not in chunk.metadata for chunk in chunks)
    assert all("version" not in chunk.metadata for chunk in chunks)


# SPECSFY: US-005 FR-008 AC-017
def test_type_and_version_do_not_affect_splitter_choice_or_blocking() -> None:
    document = _document(["500 MEGA"])
    document.metadata["type"] = "procedimento"
    document.metadata["version"] = "2"

    chunks = chunk_documents([document], _config(), project_id="base")

    assert chunks
    assert all(chunk.metadata["chunk_type"] == "detail" for chunk in chunks)
