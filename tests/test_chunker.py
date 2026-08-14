from langchain_core.documents import Document

from src.chunker import chunk_documents


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
