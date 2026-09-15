"""Protótipo de comparação da SPEC-0014 (T007).

Implementação mínima, isolada em `tests/spec0014/`, que compara o controle
`atual` com as três alternativas de colocação do resumo de seção. Nunca
constrói vector store de produção: todo índice usado aqui vem de
`ProviderFactory.create_vector_store("in_memory")` (PR-001, FIND-ARCH-001).

Parâmetros congelados (seção 8 da spec): `text-embedding-3-small`, 1536
dimensões, `top_k=4`, `limiar=0.5`, `candidate_k=12`, `summary_weight=0.85`,
`route_top_k=1`, `route_threshold=0.5`.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from langchain_core.documents import Document

from src.pipeline.providers.contracts import LogicalScope, VectorRecord
from src.pipeline.providers.factory import ProviderFactory

_TOP_K = 4
_LIMIAR = 0.5
_CANDIDATE_K = 12
_SUMMARY_WEIGHT = 0.85
_ROUTE_TOP_K = 1
_ROUTE_THRESHOLD = 0.5
_CUSTO = {"atual": 0, "metadado": 1, "chunk_com_peso": 2, "indice_de_roteamento": 3}
_PARAMETROS = {
    "atual": {"chunker": {}, "recuperacao": {"top_k": _TOP_K}},
    "metadado": {
        "chunker": {"section_summary_placement": "metadata"},
        "recuperacao": {"top_k": _TOP_K},
    },
    "chunk_com_peso": {
        "chunker": {},
        "recuperacao": {
            "top_k": _TOP_K,
            "candidate_k": _CANDIDATE_K,
            "summary_weight": _SUMMARY_WEIGHT,
        },
    },
    "indice_de_roteamento": {
        "chunker": {},
        "recuperacao": {
            "top_k": _TOP_K,
            "route_top_k": _ROUTE_TOP_K,
            "route_threshold": _ROUTE_THRESHOLD,
        },
    },
}
_IMPACTAM_CHUNK_TYPE = {"metadado", "indice_de_roteamento"}


def _section_key(metadata: dict) -> str:
    return (
        f"{metadata.get('document_id', '')}|"
        f"{metadata.get('titulo', '')}|"
        f"{metadata.get('secao', '')}"
    )


def projetar_estrategia(nome: str, chunks: list[Document]) -> dict:
    """Define, sem consultar nada, o que cada estratégia indexa e busca."""
    if nome == "atual":
        return {"searchable": list(chunks), "top_k": _TOP_K}

    if nome == "chunk_com_peso":
        return {
            "searchable": list(chunks),
            "top_k": _TOP_K,
            "candidate_k": _CANDIDATE_K,
            "summary_weight": _SUMMARY_WEIGHT,
        }

    if nome == "metadado":
        resumos = {
            _section_key(chunk.metadata): chunk.page_content
            for chunk in chunks
            if chunk.metadata.get("chunk_type") == "section_summary"
        }
        detalhes = []
        for chunk in chunks:
            if chunk.metadata.get("chunk_type") == "section_summary":
                continue
            chave = _section_key(chunk.metadata)
            detalhes.append(
                Document(
                    page_content=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        "section_key": chave,
                        "section_summary_text": resumos.get(chave, ""),
                    },
                )
            )
        return {"searchable": detalhes, "top_k": _TOP_K}

    if nome == "indice_de_roteamento":
        router: list[Document] = []
        detalhes = []
        for chunk in chunks:
            chave = _section_key(chunk.metadata)
            enriquecido = Document(
                page_content=chunk.page_content,
                metadata={**chunk.metadata, "section_key": chave},
            )
            if chunk.metadata.get("chunk_type") == "section_summary":
                router.append(enriquecido)
            else:
                detalhes.append(enriquecido)
        return {
            "router": router,
            "searchable": detalhes,
            "top_k": _TOP_K,
            "route_top_k": _ROUTE_TOP_K,
            "route_threshold": _ROUTE_THRESHOLD,
        }

    raise ValueError(f"estratégia desconhecida: {nome!r}")


def reranquear_com_peso(
    pontuados: list[tuple[float, Document]], peso: float = _SUMMARY_WEIGHT
) -> list[tuple[float, Document]]:
    """Penaliza somente resumos de seção antes de ordenar por score final."""
    ajustados = [
        (score * peso, doc) if doc.metadata.get("chunk_type") == "section_summary" else (score, doc)
        for score, doc in pontuados
    ]
    return sorted(ajustados, key=lambda item: item[0], reverse=True)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return dot / (norma_a * norma_b)


def _indexar(
    docs: list[Document], embeddings, providers_usados: list[str]
) -> tuple[object, LogicalScope]:
    """Cria um índice `in_memory` pela factory e grava os documentos."""
    adapter = ProviderFactory.create_vector_store("in_memory")
    providers_usados.append("in_memory")
    scope = LogicalScope(project_id="spec0014")
    adapter.ensure_ready(scope, dimensions=len(embeddings.embed_query(" ")))
    if docs:
        vetores = embeddings.embed_documents([doc.page_content for doc in docs])
        registros = [
            VectorRecord(
                id=str(doc.metadata.get("chunk_id") or f"chunk-{index}"),
                content=doc.page_content,
                vector=vetor,
                metadata=doc.metadata,
            )
            for index, (doc, vetor) in enumerate(zip(docs, vetores, strict=False))
        ]
        adapter.upsert(scope, registros)
    return adapter, scope


def _avaliar_consulta(case, resultados, limiar: float) -> dict:
    """Aprova/mede ruído e colisão de uma consulta, sobre resultados neutros."""
    if case.categoria == "sem_resposta":
        melhor = max((item.score for item in resultados), default=0.0)
        ruido = sum(1 for item in resultados if item.score >= limiar)
        aprovada = melhor < limiar
    else:
        textos = [str(item.content or "") for item in resultados]
        ruido = sum(
            1 for texto in textos if not any(termo in texto for termo in case.deve_conter)
        )
        combinado = "\n".join(textos)
        aprovada = all(termo in combinado for termo in case.deve_conter)

    secoes_por_tipo: dict[str, set[str]] = {"section_summary": set(), "detail": set()}
    for item in resultados:
        tipo = item.metadata.get("chunk_type")
        chave = item.metadata.get("section_key") or _section_key(dict(item.metadata))
        if tipo in secoes_por_tipo:
            secoes_por_tipo[tipo].add(chave)
    colisao = bool(secoes_por_tipo["section_summary"] & secoes_por_tipo["detail"])

    return {"aprovada": aprovada, "ruido": ruido, "colisao": colisao}


def _rodar_estrategia(
    nome: str,
    chunks: list[Document],
    cases,
    embeddings,
    indice_erro: int | None,
    providers_usados: list[str],
) -> dict:
    plano = projetar_estrategia(nome, chunks)

    if nome == "indice_de_roteamento":
        adapter_router, scope_router = _indexar(plano["router"], embeddings, providers_usados)
        vetores_detalhe = (
            embeddings.embed_documents([doc.page_content for doc in plano["searchable"]])
            if plano["searchable"]
            else []
        )
        detalhes_com_vetor = list(zip(plano["searchable"], vetores_detalhe, strict=False))
    else:
        adapter, scope = _indexar(plano["searchable"], embeddings, providers_usados)

    total = len(cases)
    aprovadas = 0
    ruido_total = 0
    colisoes_total = 0

    for indice, case in enumerate(cases):
        if indice_erro is not None and indice == indice_erro:
            raise RuntimeError(f"erro simulado em {nome!r} na consulta {indice}")

        vetor_consulta = embeddings.embed_query(case.pergunta)

        if nome == "chunk_com_peso":
            candidatos = adapter.query(scope, vetor_consulta, plano["candidate_k"])
            pontuados = [
                (item.score, Document(page_content=item.content, metadata=dict(item.metadata)))
                for item in candidatos
            ]
            reranqueados = reranquear_com_peso(pontuados, plano["summary_weight"])[: plano["top_k"]]
            resultados = [
                type(candidatos[0])(content=doc.page_content, metadata=doc.metadata, score=score)
                for score, doc in reranqueados
            ] if candidatos else []
        elif nome == "indice_de_roteamento":
            rota = adapter_router.query(scope_router, vetor_consulta, plano["route_top_k"])
            if rota and rota[0].score >= plano["route_threshold"]:
                chave = rota[0].metadata.get("section_key")
                da_secao = [
                    (score, doc)
                    for doc, vetor in detalhes_com_vetor
                    for score in [_cosine(vetor_consulta, vetor)]
                    if doc.metadata.get("section_key") == chave
                ]
                da_secao.sort(key=lambda item: item[0], reverse=True)
                melhores = da_secao[: plano["top_k"] - 1]
                resultados = [rota[0]] + [
                    type(rota[0])(content=doc.page_content, metadata=doc.metadata, score=score)
                    for score, doc in melhores
                ]
            else:
                pontuados = [
                    (_cosine(vetor_consulta, vetor), doc) for doc, vetor in detalhes_com_vetor
                ]
                pontuados.sort(key=lambda item: item[0], reverse=True)
                resultados = [
                    type(rota[0])(content=doc.page_content, metadata=doc.metadata, score=score)
                    if rota
                    else None
                    for score, doc in pontuados[: plano["top_k"]]
                ]
                resultados = [item for item in resultados if item is not None]
        else:
            resultados = adapter.query(scope, vetor_consulta, plano["top_k"])

        avaliacao = _avaliar_consulta(case, resultados, _LIMIAR)
        aprovadas += int(avaliacao["aprovada"])
        ruido_total += avaliacao["ruido"]
        colisoes_total += int(avaliacao["colisao"])

    regressoes = [] if aprovadas == total else ["aprovação perdida em relação ao total"]

    return {
        "status": "concluido",
        "total": total,
        "aprovadas": aprovadas,
        "regressoes": regressoes,
        "ruido": ruido_total,
        "colisoes": colisoes_total,
    }


def _hash_file(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _hash_corpus(chunks: list[Document]) -> str:
    conteudo = " ".join(chunk.page_content for chunk in chunks)
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def comparar_todas(
    *,
    input_dir: str | None = None,
    gabarito_path: str | None = None,
    chunks: list[Document] | None = None,
    cases=None,
    embeddings=None,
    simular_erro: dict[str, int] | None = None,
) -> dict:
    """Roda o controle e as três alternativas na mesma rodada.

    Aceita `chunks`/`cases`/`embeddings` diretos (uso em teste, sem tocar
    disco ou API real) ou `input_dir`/`gabarito_path` (uso real, T008).
    """
    simular_erro = simular_erro or {}

    if chunks is None:
        from src.pipeline.chunker import chunk_documents
        from src.pipeline.loader import load_markdown_documents

        documentos = load_markdown_documents(input_dir)
        chunks = chunk_documents(
            documentos,
            {"generate_section_summaries": True, "section_summary_min_children": 3},
            project_id="spec0014",
        )

    if cases is None:
        from src.pipeline.validation import load_query_cases

        cases = load_query_cases(gabarito_path)

    if embeddings is None:
        embeddings = ProviderFactory.create_embedding(
            "openai", {"model": "text-embedding-3-small", "dimensions": 1536}
        )

    providers_usados: list[str] = []
    resultados: dict[str, dict] = {}
    for nome in ("atual", "metadado", "chunk_com_peso", "indice_de_roteamento"):
        try:
            resultados[nome] = _rodar_estrategia(
                nome, chunks, cases, embeddings, simular_erro.get(nome), providers_usados
            )
        except Exception as erro:  # noqa: BLE001 - falha de uma estratégia não aborta as demais
            resultados[nome] = {
                "status": "falhou",
                "erro": str(erro),
                "total": len(cases),
                "aprovadas": 0,
                "regressoes": [],
                "ruido": 0,
                "colisoes": 0,
            }

    if any(resultado["status"] != "concluido" for resultado in resultados.values()):
        return {"status": "inconclusivo", "estrategias": resultados, "decisao": None}

    decisao = decidir(resultados)
    saida = {"status": "concluido", "estrategias": resultados, "decisao": decisao}
    if input_dir is not None and gabarito_path is not None:
        saida["config"] = {
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "top_k": _TOP_K,
            "threshold": _LIMIAR,
        }
        saida["corpus_sha256"] = _hash_corpus(chunks)
        saida["gabarito_sha256"] = _hash_file(gabarito_path)
    return saida


def decidir(comparacao: dict[str, dict]) -> dict:
    """Aplica a regra objetiva: sem regressão, depois ruído, colisões e custo."""
    atual = comparacao["atual"]
    if atual["aprovadas"] != atual["total"]:
        return {"status": "inconclusiva", "estrategia": None}

    elegiveis = {
        nome: resultado
        for nome, resultado in comparacao.items()
        if nome == "atual" or not resultado["regressoes"]
    }

    candidatos = sorted(
        elegiveis.items(),
        key=lambda item: (item[1]["ruido"], item[1]["colisoes"], _CUSTO[item[0]]),
    )
    vencedor, resultado_vencedor = candidatos[0]

    valores_unicos = {
        (resultado["ruido"], resultado["colisoes"]) for resultado in comparacao.values()
    }
    limitacao = "gabarito não diferenciou as estratégias" if len(valores_unicos) == 1 else None

    parametros = _PARAMETROS[vencedor]
    impacto = vencedor in _IMPACTAM_CHUNK_TYPE

    return {
        "status": "concluida",
        "estrategia": vencedor,
        "criterio": ["sem_regressao", "ruido", "colisoes", "custo"],
        "justificativa": (
            f"{vencedor} venceu com ruído={resultado_vencedor['ruido']}, "
            f"colisões={resultado_vencedor['colisoes']}, custo={_CUSTO[vencedor]}."
        ),
        "parametros_chunker": parametros["chunker"],
        "parametros_recuperacao": parametros["recuperacao"],
        "impacto_chunk_type": impacto,
        "revisar_quality": impacto,
        "limitacao": limitacao,
    }
