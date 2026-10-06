"""Regras do fluxo de ingestão em etapas (SPEC-0026): arquivos, divisão e prévia.

Sem banco e sem HTTP além de ``HTTPException``: o router `ingestao` e o de
`bases` compartilham a leitura de arquivos e a validação dos parâmetros de
divisão, e o worker usa ``montar_chunking`` para aplicar exatamente a mesma
configuração que a prévia mostrou.
"""

from __future__ import annotations

import statistics
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

__all__ = [
    "BASE_PREPARADA_DIR",
    "CHUNK_SIZE_MAX",
    "CHUNK_SIZE_MIN",
    "MAX_ARQUIVOS",
    "MAX_BYTES_POR_ARQUIVO",
    "MAX_BYTES_TOTAL",
    "PADROES",
    "SPLITTERS",
    "calcular_previa",
    "ler_arquivos_markdown",
    "ler_base_preparada",
    "montar_chunking",
    "validar_parametros_divisao",
]

MAX_ARQUIVOS = 50
MAX_BYTES_POR_ARQUIVO = 5 * 1024 * 1024
MAX_BYTES_TOTAL = 50 * 1024 * 1024
BASE_PREPARADA_DIR = Path("documentos/base_exemplo")

SPLITTERS = ("header", "recursive")
CHUNK_SIZE_MIN = 200
CHUNK_SIZE_MAX = 4000
OVERLAP_MAX_FRACAO = 0.5
# Espelham `chunking` de config.yaml (header, 1000 e 200); `src/app` não lê o YAML.
PADROES = {"splitter": "header", "chunk_size": 1000, "chunk_overlap": 200}
_CHAVES_DE_CONFIGURACAO_PROPRIA = (
    "splitter",
    "chunk_size_recommended",
    "chunk_overlap_recommended",
)


def ler_base_preparada() -> list[tuple[str, bytes]]:
    return [
        (arquivo.name, arquivo.read_bytes()) for arquivo in sorted(BASE_PREPARADA_DIR.glob("*.md"))
    ]


async def ler_arquivos_markdown(arquivos: list[UploadFile]) -> list[tuple[str, bytes]]:
    """Valida o envio (quantidade, extensão, UTF-8 e tamanhos) e devolve nome e bytes."""
    if not arquivos:
        raise HTTPException(
            status_code=400, detail="Envie ao menos um arquivo .md ou use a base preparada."
        )
    if len(arquivos) > MAX_ARQUIVOS:
        raise HTTPException(status_code=400, detail=f"Limite de {MAX_ARQUIVOS} arquivos excedido.")
    conteudos: list[tuple[str, bytes]] = []
    total = 0
    for arquivo in arquivos:
        dados = await arquivo.read()
        # Path.name descarta qualquer diretório embutido no filename (ex.:
        # "../../tmp/evil.md"), antes de qualquer gravação.
        nome = Path(arquivo.filename or "").name
        if not nome or not nome.endswith(".md"):
            raise HTTPException(status_code=400, detail=f"Extensão inválida: {nome}.")
        if len(dados) > MAX_BYTES_POR_ARQUIVO:
            raise HTTPException(status_code=400, detail=f"Arquivo {nome} excede o limite de 5 MB.")
        try:
            dados.decode("utf-8")
        except UnicodeDecodeError as erro:
            raise HTTPException(
                status_code=400, detail=f"Arquivo {nome} não é UTF-8 válido."
            ) from erro
        total += len(dados)
        if total > MAX_BYTES_TOTAL:
            raise HTTPException(status_code=400, detail="Limite de 50 MB por envio excedido.")
        conteudos.append((nome, dados))
    return conteudos


def limites() -> dict[str, Any]:
    return {
        "chunk_size": {"min": CHUNK_SIZE_MIN, "max": CHUNK_SIZE_MAX},
        "chunk_overlap": {"min": 0, "max_fracao": OVERLAP_MAX_FRACAO},
    }


def validar_parametros_divisao(splitter: str, chunk_size: int, chunk_overlap: int) -> None:
    """Splitter conhecido, tamanho de 200 a 4000 e overlap de 0 até metade do tamanho."""
    if splitter not in SPLITTERS:
        raise HTTPException(
            status_code=422, detail="Splitter desconhecido. Use header ou recursive."
        )
    if not CHUNK_SIZE_MIN <= chunk_size <= CHUNK_SIZE_MAX:
        raise HTTPException(
            status_code=422,
            detail=f"O tamanho do chunk deve ficar entre {CHUNK_SIZE_MIN} e {CHUNK_SIZE_MAX}.",
        )
    if not 0 <= chunk_overlap <= chunk_size * OVERLAP_MAX_FRACAO:
        raise HTTPException(
            status_code=422,
            detail="O overlap deve ser de 0 até a metade do tamanho do chunk.",
        )


def montar_chunking(splitter: str, chunk_size: int, chunk_overlap: int) -> dict[str, Any]:
    """Seção `chunking` da fachada, igual para a prévia e para a execução."""
    return {
        "default_splitter": splitter,
        "default_chunk_size": chunk_size,
        "default_chunk_overlap": chunk_overlap,
        "generate_section_summaries": True,
        "section_summary_min_children": 3,
    }


def calcular_previa(
    conteudos: list[tuple[str, bytes]],
    chunking: dict[str, Any],
    *,
    pagina: int,
    tamanho_pagina: int,
    documento: str | None,
) -> dict[str, Any]:
    """Divide os arquivos em diretório temporário e devolve resumo e uma página de chunks."""
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    with tempfile.TemporaryDirectory(prefix="previa-") as pasta:
        for nome, dados in conteudos:
            (Path(pasta) / nome).write_bytes(dados)
        config = {
            "projeto": {"nome": "previa"},
            "caminhos": {"input_dir": pasta, "chunks_file": f"{pasta}/chunks.json"},
            "embedding": {"provider": "fake", "model": "previa", "dimensions": 8},
            "vector_store": {"provider": "qdrant", "collection_name": "previa"},
            "chunking": chunking,
        }
        resultado = service.preview_chunks(config, input_dir=pasta)
        documentos = list(resultado.documents)
        chunks = list(resultado.chunks)

    proprios = sorted(
        {
            doc.metadata.get("nome_arquivo", "")
            for doc in documentos
            if any(doc.metadata.get(chave) for chave in _CHAVES_DE_CONFIGURACAO_PROPRIA)
        }
    )
    avisos = []
    if not chunks:
        avisos.append("Nenhum chunk foi gerado com estes arquivos e parâmetros.")
    if proprios:
        avisos.append(
            "Estes arquivos têm configuração própria no frontmatter e ignoram o formulário: "
            + ", ".join(proprios)
            + "."
        )
    itens = [
        {
            "documento": chunk.metadata.get("nome_arquivo", ""),
            "posicao": int(chunk.metadata.get("chunk_index", 0)),
            "tamanho": len(chunk.page_content),
            "texto": chunk.page_content,
            "tipo": chunk.metadata.get("chunk_type", "detail"),
        }
        for chunk in chunks
    ]
    filtrados = [item for item in itens if documento is None or item["documento"] == documento]
    inicio = (pagina - 1) * tamanho_pagina
    return {
        "resumo": {
            "documentos": len(documentos),
            "chunks": len(itens),
            "tamanho_medio": round(statistics.fmean(i["tamanho"] for i in itens)) if itens else 0,
        },
        "avisos": avisos,
        "arquivos_com_configuracao_propria": proprios,
        "chunks": filtrados[inicio : inicio + tamanho_pagina],
        "pagina": pagina,
        "total": len(filtrados),
    }
