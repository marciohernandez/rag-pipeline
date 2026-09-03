"""
Pipeline RAG - Chunker
Divide documentos em chunks usando a estrategia definida no frontmatter
ou no config.yaml. Suporta: MarkdownHeaderTextSplitter e RecursiveCharacterTextSplitter.

Apos o split, injeta automaticamente o breadcrumb de headings no page_content
de cada chunk, para que o LLM saiba de qual capitulo/subcapitulo veio o conteudo.
"""

import logging
from copy import deepcopy

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.pipeline.identity import assign_chunk_identities, assign_document_identity

logger = logging.getLogger(__name__)


def _get_splitter_config(doc_metadata: dict, global_cfg: dict) -> tuple[str, int, int]:
    """
    Determina estrategia, tamanho e overlap do chunk.
    Prioridade: frontmatter do arquivo > config.yaml global.
    """
    splitter = doc_metadata.get("splitter") or global_cfg.get("default_splitter", "header")
    chunk_size = int(
        doc_metadata.get("chunk_size_recommended")
        or global_cfg.get("default_chunk_size", 1000)
    )
    chunk_overlap = int(
        doc_metadata.get("chunk_overlap_recommended")
        or global_cfg.get("default_chunk_overlap", 200)
    )
    return splitter, chunk_size, chunk_overlap


def _build_heading_breadcrumb(metadata: dict) -> str:
    """
    Monta o caminho de headings (capitulo > subcapitulo) do chunk.

    O MarkdownHeaderTextSplitter extrai titulo/secao/subsecao para o metadata.
    Esta funcao reconstroi o caminho e o coloca de volta no texto,
    para que o LLM saiba exatamente de qual parte do documento veio o conteudo.

    Exemplo:
        metadata = {titulo: "Fluxo de Atendimento",
                    secao: "Fase 3 - Orientacao para o App",
                    subsecao: "Passo a passo"}

        resultado: "[Fluxo de Atendimento > Fase 3 - Orientacao para o App > Passo a passo]"
    """
    partes = []
    for chave in ["titulo", "secao", "subsecao"]:
        valor = metadata.get(chave, "")
        if valor:
            partes.append(valor)
    if partes:
        return "[" + " > ".join(partes) + "]"
    return ""


def _split_by_headers(
    doc: Document,
    headers_config: list[list[str]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """
    Usa MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter.

    Fluxo:
    1. Divide o documento nos headers Markdown (#, ##, ###)
    2. Se algum chunk ainda for maior que chunk_size, divide por caracteres
    3. Injeta o breadcrumb de headings no inicio do page_content de cada chunk
    """
    headers_to_split = [(h[0], h[1]) for h in headers_config]
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split,
        strip_headers=False,
    )

    header_chunks = header_splitter.split_text(doc.page_content)

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    final_chunks: list[Document] = []
    for chunk in header_chunks:
        merged_metadata = {**doc.metadata, **chunk.metadata}

        if len(chunk.page_content) > chunk_size:
            sub_chunks = char_splitter.create_documents(
                [chunk.page_content], metadatas=[merged_metadata]
            )
            final_chunks.extend(sub_chunks)
        else:
            chunk.metadata = merged_metadata
            final_chunks.append(chunk)

    # --- BREADCRUMB INJECTION ---
    # Coloca o caminho de headings no inicio do page_content.
    # Antes: "Objecao: Nao preciso antecipar..."
    # Depois: "[Book de Objecoes > ANTECIPACAO DE RECEBIVEIS]\n\nObjecao: Nao preciso antecipar..."
    for chunk in final_chunks:
        breadcrumb = _build_heading_breadcrumb(chunk.metadata)
        if breadcrumb:
            chunk.metadata["breadcrumb"] = breadcrumb
            chunk.page_content = breadcrumb + "\n\n" + chunk.page_content

    return final_chunks


def _split_by_characters(
    doc: Document,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Usa RecursiveCharacterTextSplitter puro."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.create_documents([doc.page_content], metadatas=[doc.metadata])


def _split_by_qa(doc: Document) -> list[Document]:
    """Divide o corpo por blocos separados por ``++++`` (formato Q&A).

    Cada bloco não vazio vira exatamente um chunk, independentemente do
    tamanho: um par pergunta/resposta nunca é cortado por chunk_size.
    """
    blocos = [bloco.strip() for bloco in doc.page_content.split("++++")]
    return [
        Document(page_content=bloco, metadata=dict(doc.metadata))
        for bloco in blocos
        if bloco
    ]


def _section_summary_chunks(chunks: list[Document], min_children: int) -> list[Document]:
    """Cria um resumo determinístico para seções com várias subseções."""
    grouped: dict[tuple[str, str, str], list[Document]] = {}
    for chunk in chunks:
        metadata = chunk.metadata
        section = metadata.get("secao", "")
        subsection = metadata.get("subsecao", "")
        if not section or not subsection:
            continue
        key = (
            metadata.get("caminho_relativo", ""),
            metadata.get("titulo", ""),
            section,
        )
        grouped.setdefault(key, []).append(chunk)

    summaries: list[Document] = []
    for (_, title, section), section_chunks in grouped.items():
        titles: list[str] = []
        for chunk in section_chunks:
            subsection = chunk.metadata.get("subsecao", "")
            if subsection and subsection not in titles:
                titles.append(subsection)
        if len(titles) < min_children:
            continue

        source_metadata = deepcopy(section_chunks[0].metadata)
        source_metadata.update(
            {
                "chunk_type": "section_summary",
                "subsecao": "",
                "summary_child_count": len(titles),
                "summary_key": f"{title}|{section}",
            }
        )
        breadcrumb = _build_heading_breadcrumb(source_metadata)
        source_metadata["breadcrumb"] = breadcrumb
        content = "Itens disponíveis nesta seção:\n" + "\n".join(
            f"- {item}" for item in titles
        )
        if breadcrumb:
            content = f"{breadcrumb}\n\n{content}"
        summaries.append(Document(page_content=content, metadata=source_metadata))
    return summaries


def chunk_documents(
    documents: list[Document],
    chunking_cfg: dict,
    *,
    project_id: str = "default",
) -> list[Document]:
    """
    Processa uma lista de documentos e retorna todos os chunks.
    Adiciona ao metadata: chunk_index, total_chunks, breadcrumb.
    """
    headers_config = chunking_cfg.get(
        "headers_to_split_on", [["#", "titulo"], ["##", "secao"], ["###", "subsecao"]]
    )

    all_chunks: list[Document] = []
    generate_summaries = bool(chunking_cfg.get("generate_section_summaries", False))
    min_summary_children = int(chunking_cfg.get("section_summary_min_children", 3))

    for doc in documents:
        nome_arquivo = doc.metadata.get("nome_arquivo", "desconhecido")
        assign_document_identity(doc, project_id)
        splitter_type, chunk_size, chunk_overlap = _get_splitter_config(
            doc.metadata, chunking_cfg
        )

        try:
            if splitter_type == "qa":
                chunks = _split_by_qa(doc)
            elif splitter_type == "MarkdownHeaderTextSplitter" or splitter_type == "header":
                chunks = _split_by_headers(doc, headers_config, chunk_size, chunk_overlap)
            else:
                chunks = _split_by_characters(doc, chunk_size, chunk_overlap)

            for chunk in chunks:
                chunk.metadata["chunk_type"] = "detail"
                chunk.metadata.setdefault("nome_arquivo", nome_arquivo)

            if generate_summaries:
                chunks = _section_summary_chunks(chunks, min_summary_children) + chunks

            total = len(chunks)
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = total

            all_chunks.extend(chunks)
            logger.info(
                "Chunks de %s: %d (splitter=%s, size=%d, overlap=%d)",
                nome_arquivo, total, splitter_type, chunk_size, chunk_overlap,
            )

        except Exception as e:
            logger.error("Erro ao chunkar %s: %s", nome_arquivo, e)
            raise RuntimeError(
                f"Falha ao chunkar '{nome_arquivo}'; indexação cancelada."
            ) from e

    assign_chunk_identities(all_chunks, project_id)
    logger.info("Total de chunks gerados: %d", len(all_chunks))
    return all_chunks
