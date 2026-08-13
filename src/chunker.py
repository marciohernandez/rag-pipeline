"""
Pipeline RAG - Chunker
Divide documentos em chunks usando a estrategia definida no frontmatter
ou no config.yaml. Suporta: MarkdownHeaderTextSplitter e RecursiveCharacterTextSplitter.

Apos o split, injeta automaticamente o breadcrumb de headings no page_content
de cada chunk, para que o LLM saiba de qual capitulo/subcapitulo veio o conteudo.
"""

import logging
from copy import deepcopy

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

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


def chunk_documents(
    documents: list[Document],
    chunking_cfg: dict,
) -> list[Document]:
    """
    Processa uma lista de documentos e retorna todos os chunks.
    Adiciona ao metadata: chunk_index, total_chunks, breadcrumb.
    """
    headers_config = chunking_cfg.get(
        "headers_to_split_on", [["#", "titulo"], ["##", "secao"], ["###", "subsecao"]]
    )

    all_chunks: list[Document] = []

    for doc in documents:
        nome_arquivo = doc.metadata.get("nome_arquivo", "desconhecido")
        splitter_type, chunk_size, chunk_overlap = _get_splitter_config(
            doc.metadata, chunking_cfg
        )

        try:
            if splitter_type == "MarkdownHeaderTextSplitter" or splitter_type == "header":
                chunks = _split_by_headers(doc, headers_config, chunk_size, chunk_overlap)
            else:
                chunks = _split_by_characters(doc, chunk_size, chunk_overlap)

            total = len(chunks)
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = total
                chunk.metadata.setdefault("nome_arquivo", nome_arquivo)

            all_chunks.extend(chunks)
            logger.info(
                "Chunks de %s: %d (splitter=%s, size=%d, overlap=%d)",
                nome_arquivo, total, splitter_type, chunk_size, chunk_overlap,
            )

        except Exception as e:
            logger.error("Erro ao chunkar %s: %s", nome_arquivo, e)
            continue

    logger.info("Total de chunks gerados: %d", len(all_chunks))
    return all_chunks
