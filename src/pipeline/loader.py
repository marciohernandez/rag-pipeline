"""
Pipeline RAG — Loader de Documentos Markdown
Carrega arquivos .md preservando frontmatter YAML como metadata.
"""

import logging
import re
from hashlib import sha256
from pathlib import Path

import yaml
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentLoadError(RuntimeError):
    """Impede indexação parcial quando uma fonte não pode ser carregada."""


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extrai frontmatter YAML do topo do arquivo Markdown.
    Retorna (metadata_dict, body_sem_frontmatter).
    """
    # Remove BOM (\ufeff) caso o arquivo tenha sido salvo com UTF-8 BOM (comum no Windows)
    content = content.lstrip("\ufeff")
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)

    if match:
        raw_yaml = match.group(1)
        body = content[match.end() :]
        try:
            metadata = yaml.safe_load(raw_yaml) or {}
            # Garante que todos os valores são serializáveis como string (ChromaDB requer)
            metadata = _sanitize_metadata(metadata)
        except yaml.YAMLError as e:
            logger.warning("Erro ao parsear frontmatter YAML: %s", e)
            metadata = {}
        return metadata, body
    else:
        return {}, content


def _sanitize_metadata(metadata: dict) -> dict:
    """
    Converte listas e booleanos do frontmatter em tipos compatíveis
    com ChromaDB (str, int, float, bool — sem listas).
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            sanitized[key] = ", ".join(str(v) for v in value)
        elif value is None:
            sanitized[key] = ""
        else:
            sanitized[key] = value
    return sanitized


def load_markdown_documents(input_dir: str, *, strict: bool = True) -> list[Document]:
    """
    Carrega todos os arquivos .md de input_dir.
    Cada arquivo se torna um Document com:
      - page_content: corpo do markdown (sem frontmatter)
      - metadata: frontmatter YAML + nome_arquivo + caminho_relativo
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Diretório de entrada não encontrado: {input_path.resolve()}")

    md_files = sorted(input_path.glob("*.md"))
    if not md_files:
        raise ValueError(f"Nenhum arquivo .md encontrado em: {input_path.resolve()}")

    documents: list[Document] = []

    for file_path in md_files:
        try:
            # utf-8-sig remove automaticamente o BOM (\ufeff) de arquivos Windows
            content = file_path.read_text(encoding="utf-8-sig")
            frontmatter, body = _parse_frontmatter(content)

            # Metadados base sempre presentes
            base_metadata = {
                "nome_arquivo": file_path.name,
                "caminho_relativo": str(file_path.relative_to(input_path)),
                **frontmatter,
            }

            normalized_body = body.strip()
            base_metadata["source_hash"] = sha256(content.encode("utf-8")).hexdigest()
            doc = Document(page_content=normalized_body, metadata=base_metadata)
            documents.append(doc)
            logger.info("✓ Carregado: %s (%d chars)", file_path.name, len(body))

        except Exception as e:
            if strict:
                raise DocumentLoadError(
                    f"Falha ao carregar '{file_path}'; indexação cancelada."
                ) from e
            logger.error("✗ Erro ao carregar %s: %s", file_path.name, e)
            continue

    logger.info("Total de documentos carregados: %d / %d", len(documents), len(md_files))
    return documents
