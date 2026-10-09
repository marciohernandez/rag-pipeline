"""Regras do fluxo de ingestão em etapas (SPEC-0026): arquivos, divisão e prévia.

Sem banco e sem HTTP além de ``HTTPException``: o router `ingestao` e o de
`bases` compartilham a leitura de arquivos e a validação dos parâmetros de
divisão, e o worker usa ``montar_chunking`` para aplicar exatamente a mesma
configuração que a prévia mostrou.
"""

from __future__ import annotations

import json
import statistics
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

__all__ = [
    "BASE_PREPARADA_DIR",
    "CHUNK_SIZE_MAX",
    "CHUNK_SIZE_MIN",
    "ESTRATEGIAS",
    "MAX_ARQUIVOS",
    "MAX_BYTES_POR_ARQUIVO",
    "MAX_BYTES_TOTAL",
    "PADROES",
    "PADROES_PROCESSAMENTO",
    "SPLITTERS",
    "calcular_previa",
    "ler_arquivos_markdown",
    "ler_base_preparada",
    "ler_processamento",
    "montar_chunking",
    "secoes_de_processamento",
    "validar_parametros_divisao",
]

MAX_ARQUIVOS = 50
MAX_BYTES_POR_ARQUIVO = 5 * 1024 * 1024
MAX_BYTES_TOTAL = 50 * 1024 * 1024
BASE_PREPARADA_DIR = Path("documentos/base_exemplo")

SPLITTERS = ("header", "markdown", "markdown_syntax", "recursive", "character_split", "token")
# Rótulos e campos de cada estratégia, devolvidos por `GET /padroes` (SPEC-0029).
ESTRATEGIAS = [
    {
        "valor": "header",
        "rotulo": "Markdown por cabeçalhos",
        "campos": ["tamanho", "overlap", "nivel_cabecalho"],
    },
    {
        "valor": "markdown",
        "rotulo": "Markdown recursivo",
        "campos": ["tamanho", "overlap", "nivel_cabecalho"],
    },
    {
        "valor": "markdown_syntax",
        "rotulo": "Markdown sintático",
        "campos": ["nivel_cabecalho", "remover_cabecalhos"],
    },
    {"valor": "recursive", "rotulo": "Recursivo por caracteres", "campos": ["tamanho", "overlap"]},
    {
        "valor": "character_split",
        "rotulo": "Por caractere",
        "campos": ["tamanho", "overlap", "separador"],
    },
    {"valor": "token", "rotulo": "Por tokens", "campos": ["tamanho", "overlap", "encoding"]},
]
_COM_RESUMOS = ("header", "markdown_syntax")
_SEM_TAMANHO = ("markdown_syntax",)
TOKEN_SIZE_MIN = 50
TOKEN_SIZE_MAX = 2000
ENCODINGS = ("cl100k_base", "o200k_base")
NIVEL_MAX = 6
SEPARADOR_MAX = 10
MINIMO_SUBSECOES = (2, 10)
MINIMO_UTIL = (0, 1000)
STATUS_MAX = 20
STATUS_TAMANHO_MAX = 40
BATCH_SIZE = (1, 500)
SYNC_MODES = ("append", "mirror")
_MARCAS = ("#", "##", "###", "####", "#####", "######")
_CHAVES_DE_NIVEL = ("titulo", "secao", "subsecao", "nivel_4", "nivel_5", "nivel_6")
CHUNK_SIZE_MIN = 200
CHUNK_SIZE_MAX = 4000
OVERLAP_MAX_FRACAO = 0.5
# Espelham `chunking` de config.yaml (header, 1000 e 200); `src/app` não lê o YAML.
PADROES = {"splitter": "header", "chunk_size": 1000, "chunk_overlap": 200}
# Espelham config.yaml e os padrões da fachada; Bases sem estas chaves usam os mesmos valores.
PADROES_PROCESSAMENTO: dict[str, dict[str, Any]] = {
    "opcoes": {
        "nivel_cabecalho": 3,
        "separador": "\\n\\n",
        "encoding": "cl100k_base",
        "remover_cabecalhos": False,
    },
    "resumos": {"ativo": True, "minimo_subsecoes": 3},
    "qualidade": {"minimo_util": 60},
    "contrato": {"status_bloqueado": []},
    "destino": {"batch_size": 50, "sync_mode": "append"},
}
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
        "token_size": {"min": TOKEN_SIZE_MIN, "max": TOKEN_SIZE_MAX},
        "encodings": list(ENCODINGS),
        "nivel_cabecalho": {"max": NIVEL_MAX},
        "separador": {"max": SEPARADOR_MAX},
        "minimo_subsecoes": {"min": MINIMO_SUBSECOES[0], "max": MINIMO_SUBSECOES[1]},
        "minimo_util": {"min": MINIMO_UTIL[0], "max": MINIMO_UTIL[1]},
        "status_bloqueado": {"max": STATUS_MAX, "tamanho_max": STATUS_TAMANHO_MAX},
        "batch_size": {"min": BATCH_SIZE[0], "max": BATCH_SIZE[1]},
        "sync_modes": list(SYNC_MODES),
    }


def _recusar(mensagem: str) -> None:
    raise HTTPException(status_code=422, detail=mensagem)


def _inteiro(valor: Any, rotulo: str, minimo: int, maximo: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        _recusar(f"{rotulo} deve ficar entre {minimo} e {maximo}.")
    return valor


def ler_processamento(texto: str | None) -> dict[str, Any]:
    """Lê o campo de formulário `processamento` (JSON); ausente, devolve objeto vazio."""
    if texto is None or not texto.strip():
        return {}
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        _recusar("O campo processamento deve ser um JSON válido.")
    if not isinstance(dados, dict):
        _recusar("O campo processamento deve ser um objeto JSON.")
    return dados


def _grupo(processamento: dict[str, Any], nome: str) -> dict[str, Any]:
    valor = processamento.get(nome) or {}
    if not isinstance(valor, dict):
        _recusar(f"O grupo {nome} deve ser um objeto.")
    return {**PADROES_PROCESSAMENTO[nome], **valor}


def validar_parametros_divisao(
    splitter: str,
    chunk_size: int,
    chunk_overlap: int,
    processamento: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida estratégia, campos próprios, resumos, qualidade, contrato e destino.

    Devolve o processamento normalizado, com os padrões nas chaves ausentes.
    """
    if splitter not in SPLITTERS:
        _recusar("Estratégia de divisão desconhecida. Use " + ", ".join(SPLITTERS) + ".")
    dados = processamento or {}
    opcoes = _grupo(dados, "opcoes")
    if "nivel_cabecalho" not in (dados.get("opcoes") or {}):
        opcoes["nivel_cabecalho"] = 0 if splitter == "markdown" else 3
    if splitter not in _SEM_TAMANHO:
        if splitter == "token":
            minimo, maximo, unidade = TOKEN_SIZE_MIN, TOKEN_SIZE_MAX, "tokens"
        else:
            minimo, maximo, unidade = CHUNK_SIZE_MIN, CHUNK_SIZE_MAX, "caracteres"
        if not minimo <= chunk_size <= maximo:
            _recusar(f"O tamanho do chunk deve ficar entre {minimo} e {maximo} {unidade}.")
        if not 0 <= chunk_overlap <= chunk_size * OVERLAP_MAX_FRACAO:
            _recusar("O overlap deve ser de 0 até a metade do tamanho do chunk.")
    if splitter in ("header", "markdown", "markdown_syntax"):
        minimo_nivel = 0 if splitter == "markdown" else 1
        _inteiro(
            opcoes["nivel_cabecalho"], "O nível de Dividir por cabeçalhos", minimo_nivel, NIVEL_MAX
        )
    if splitter == "character_split":
        separador = opcoes["separador"]
        if not isinstance(separador, str) or not 1 <= len(separador) <= SEPARADOR_MAX:
            _recusar(f"O separador deve ter de 1 a {SEPARADOR_MAX} caracteres.")
    if splitter == "token" and opcoes["encoding"] not in ENCODINGS:
        _recusar("Encoding desconhecido. Use " + " ou ".join(ENCODINGS) + ".")
    if not isinstance(opcoes["remover_cabecalhos"], bool):
        _recusar("Remover cabeçalhos deve ser verdadeiro ou falso.")

    resumos = _grupo(dados, "resumos")
    if not isinstance(resumos["ativo"], bool):
        _recusar("Resumos de seção deve ser verdadeiro ou falso.")
    _inteiro(resumos["minimo_subsecoes"], "O mínimo de subseções", *MINIMO_SUBSECOES)

    qualidade = _grupo(dados, "qualidade")
    _inteiro(qualidade["minimo_util"], "O mínimo útil", *MINIMO_UTIL)

    contrato = _grupo(dados, "contrato")
    status = contrato["status_bloqueado"]
    if not isinstance(status, list) or len(status) > STATUS_MAX:
        _recusar(f"Informe até {STATUS_MAX} status bloqueados.")
    limpos = [item.strip() if isinstance(item, str) else "" for item in status]
    if any(not 1 <= len(item) <= STATUS_TAMANHO_MAX for item in limpos):
        _recusar(f"Cada status bloqueado deve ter de 1 a {STATUS_TAMANHO_MAX} caracteres.")
    if len(set(limpos)) != len(limpos):
        _recusar("Há status bloqueados repetidos.")
    contrato["status_bloqueado"] = limpos

    destino = _grupo(dados, "destino")
    _inteiro(destino["batch_size"], "O tamanho do lote de embeddings", *BATCH_SIZE)
    if destino["sync_mode"] not in SYNC_MODES:
        _recusar("Modo de sincronização desconhecido. Use append ou mirror.")

    return {
        "opcoes": opcoes,
        "resumos": resumos,
        "qualidade": qualidade,
        "contrato": contrato,
        "destino": destino,
    }


def _cabecalhos_ate(nivel: int) -> list[list[str]]:
    return [[_MARCAS[i], _CHAVES_DE_NIVEL[i]] for i in range(nivel)]


def _decodificar_separador(separador: str) -> str:
    return separador.replace("\\n", "\n").replace("\\t", "\t")


def montar_chunking(
    splitter: str,
    chunk_size: int,
    chunk_overlap: int,
    processamento: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seção `chunking` da fachada, igual para a prévia, a execução e a repetição."""
    dados = processamento or {}
    opcoes = {**PADROES_PROCESSAMENTO["opcoes"], **(dados.get("opcoes") or {})}
    if "nivel_cabecalho" not in (dados.get("opcoes") or {}):
        opcoes["nivel_cabecalho"] = 0 if splitter == "markdown" else 3
    resumos = {**PADROES_PROCESSAMENTO["resumos"], **(dados.get("resumos") or {})}
    nivel = int(opcoes["nivel_cabecalho"])
    chunking: dict[str, Any] = {
        "default_splitter": splitter,
        "default_chunk_size": chunk_size,
        "default_chunk_overlap": chunk_overlap,
        "generate_section_summaries": bool(resumos["ativo"]) and splitter in _COM_RESUMOS,
        "section_summary_min_children": int(resumos["minimo_subsecoes"]),
    }
    if splitter in ("header", "markdown_syntax") and nivel != 3:
        chunking["headers_to_split_on"] = _cabecalhos_ate(nivel)
    if splitter == "markdown" and nivel > 0:
        chunking["markdown_headers"] = _cabecalhos_ate(nivel)
    if splitter == "markdown_syntax":
        chunking["strip_headers"] = bool(opcoes["remover_cabecalhos"])
    if splitter == "character_split":
        chunking["separator"] = _decodificar_separador(str(opcoes["separador"]))
    if splitter == "token":
        chunking["encoding_name"] = str(opcoes["encoding"])
    return chunking


def secoes_de_processamento(processamento: dict[str, Any] | None) -> dict[str, Any]:
    """Seções `qualidade` e `contrato_markdown` da fachada; vazias quando não informadas."""
    dados = processamento or {}
    secoes: dict[str, Any] = {}
    if dados.get("qualidade"):
        secoes["qualidade"] = {"minimo_util": int(dados["qualidade"]["minimo_util"])}
    if (dados.get("contrato") or {}).get("status_bloqueado"):
        secoes["contrato_markdown"] = {
            "status_bloqueado": list(dados["contrato"]["status_bloqueado"])
        }
    return secoes


def calcular_previa(
    conteudos: list[tuple[str, bytes]],
    chunking: dict[str, Any],
    *,
    pagina: int,
    tamanho_pagina: int,
    documento: str | None,
    processamento: dict[str, Any] | None = None,
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
            **secoes_de_processamento(processamento),
        }
        resultado = service.preview_chunks(config, input_dir=pasta)
        documentos = list(resultado.documents)
        chunks = list(resultado.chunks)
        excluidos = sorted(
            registro.get("nome_arquivo") or registro.get("documento", "")
            for registro in resultado.excluded_documents
        )
        curtos = sum(
            (getattr(resultado.quality_report, "sinais", {}) or {})
            .get("conteudo_util_curto", {})
            .values()
        )

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
    if curtos:
        minimo = int(
            ((processamento or {}).get("qualidade") or PADROES_PROCESSAMENTO["qualidade"])[
                "minimo_util"
            ]
        )
        avisos.append(f"{curtos} chunks com conteúdo útil abaixo de {minimo} caracteres.")
    if excluidos:
        avisos.append("Documentos excluídos por status bloqueado: " + ", ".join(excluidos) + ".")
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
        "documentos_excluidos": excluidos,
        "chunks": filtrados[inicio : inicio + tamanho_pagina],
        "pagina": pagina,
        "total": len(filtrados),
    }
