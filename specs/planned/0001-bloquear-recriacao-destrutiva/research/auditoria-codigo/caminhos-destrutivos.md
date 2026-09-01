# Auditoria dos caminhos destrutivos do rag-ingestion-pipeline

Proveniencia: arquivos deste repositorio, commit `5ba9a56`, lidos em 2026-08-31.
Licenca: codigo proprio do projeto; copia integral permitida.
Proposito: sustentar as claims R-001 a R-004 da SPEC-0001 sem depender de leitura futura do codigo, que sera alterado por esta propria entrega.

## Caminho destrutivo alcancavel pela CLI

Sustenta R-001. A flag existe nas duas CLIs, e propagada ate a camada de indexacao e termina em exclusao remota.

### pipeline.py linhas 49-58

```python
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help=(
            "Substitui a base antes de indexar: recria a collection no Qdrant "
            "ou limpa somente o namespace no Pinecone"
        ),
    )
    return parser.parse_args()
```

### pipeline.py linhas 118,126

```python

    index_chunks(
        chunks=chunks,
        embedding_cfg=embedding_cfg,
        vector_cfg=vector_cfg,
        persist_dir=vector_store_dir,
        recreate=args.recreate,
    )

```

### upsert_from_chunks.py linhas 36,45

```python
        help="Vector store alvo para o reupsert (padrao: qdrant)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Apaga/recria a collection/namespace antes do upsert para evitar duplicacao",
    )
    parser.add_argument(
        "--manifest",
        default=None,
```

### upsert_from_chunks.py linhas 99,108

```python

    index_chunks(
        chunks=chunks,
        embedding_cfg=embedding_cfg,
        vector_cfg=vector_cfg,
        persist_dir=persist_dir,
        recreate=args.recreate,
    )

    logger.info("Reupsert concluido com sucesso.")
```

### src/embedder.py linhas 197,212 assinatura de index_chunks

```python
def index_chunks(
    chunks: list[Document],
    embedding_cfg: dict,
    vector_cfg: dict,
    persist_dir: str,
    batch_size: int = 50,
    recreate: bool = False,
) -> None:
    """
    Gera embeddings e indexa todos os chunks no vector store.
    Processa em batches para evitar timeout e exibir progresso.

    Args:
        recreate: Se True, apaga e recria a collection antes de indexar.
                  Use para re-indexar sem duplicar.
    """
```

### src/embedder.py linhas 284,292 exclusao da collection Qdrant

```python
        existing = [c.name for c in client.get_collections().collections]

        if recreate and collection in existing:
            client.delete_collection(collection)
            existing.remove(collection)
            logger.info("Collection '%s' removida para re-indexacao", collection)

        if collection not in existing:
            client.create_collection(
```

### src/embedder.py linhas 392,400 limpeza total do namespace Pinecone

```python

        index = pinecone.Index(index_name)
        if recreate:
            index.delete(delete_all=True, namespace=namespace)
            logger.info(
                "Namespace Pinecone '%s' limpo no indice '%s'",
                namespace,
                index_name,
            )
```

## Modo espelho no Qdrant

Sustenta R-002. O conjunto elegivel a remocao ja e filtrado por metadata.project_id e a remocao ocorre depois do laco de upsert.

### src/embedder.py linhas 303,322 leitura do escopo por project_id

```python

        project_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.project_id",
                    match=MatchValue(value=project_id),
                )
            ]
        )
        existing_ids: set[str] = set()
        offset = None
        while True:
            records, next_offset = client.scroll(
                collection_name=collection,
                scroll_filter=project_filter,
                limit=256,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
```

### src/embedder.py linhas 352,373 remocao posterior ao upsert

```python
                "  [%d/%d] batch indexado",
                min(i + batch_size, len(to_upsert)),
                len(to_upsert),
            )

        if sync_mode == "mirror":
            stale_ids = existing_ids - set(chunk_ids)
            stale_ids_list = sorted(stale_ids)
            for i in range(0, len(stale_ids_list), batch_size):
                stale_batch = stale_ids_list[i : i + batch_size]
                client.delete(
                    collection_name=collection,
                    points_selector=PointIdsList(points=stale_batch),
                    wait=True,
                )
                logger.info(
                    "  [%d/%d] pontos obsoletos removidos",
                    min(i + batch_size, len(stale_ids_list)),
                    len(stale_ids_list),
                )

    elif vs_provider == "pinecone":
```

### src/embedder.py linhas 268,282 validacao de escopo existente

```python
        sync_mode = vector_cfg.get("sync_mode", "append")
        if sync_mode not in {"append", "mirror"}:
            raise ValueError("vector_store.sync_mode deve ser 'append' ou 'mirror'")

        project_ids = {chunk.metadata.get("project_id", "") for chunk in chunks}
        if len(project_ids) != 1 or not next(iter(project_ids), ""):
            raise ValueError(
                "Todos os chunks Qdrant devem ter o mesmo project_id não vazio"
            )
        project_id = next(iter(project_ids))
        chunk_ids = [chunk.metadata.get("chunk_id", "") for chunk in chunks]
        if any(not chunk_id for chunk_id in chunk_ids):
            raise ValueError("Há chunks sem chunk_id; indexação cancelada.")
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Há chunk_ids duplicados; indexação cancelada.")
```

## Providers sem paridade de espelho

Sustenta R-003. Chroma apenas acumula lotes e Pinecone apenas adiciona documentos; sync_mode nao e lido em nenhum dos dois.

### src/embedder.py linhas 225,242 caminho ChromaDB

```python
    )

    if vs_provider == "chroma":
        from langchain_chroma import Chroma

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                collection_name=collection,
                persist_directory=persist_dir,
            )
            logger.info(
                "  [%d/%d] batch indexado (%d chunks)",
                min(i + batch_size, total), total, len(batch),
            )

```

### src/embedder.py linhas 401,415 caminho Pinecone

```python

        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=namespace,
        )

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            vector_store.add_documents(
                documents=batch,
                ids=_pinecone_document_ids(batch, namespace),
            )
            logger.info("  [%d/%d] batch indexado", min(i + batch_size, total), total)

```

### Ocorrencias de sync_mode no codigo de producao

```text
src/embedder.py:268:        sync_mode = vector_cfg.get("sync_mode", "append")
src/embedder.py:269:        if sync_mode not in {"append", "mirror"}:
src/embedder.py:270:            raise ValueError("vector_store.sync_mode deve ser 'append' ou 'mirror'")
src/embedder.py:333:            len(existing_ids), len(to_upsert), sync_mode,
src/embedder.py:357:        if sync_mode == "mirror":
```

## Documentacao que recomenda recriacao

Sustenta R-004. As ocorrencias abaixo apresentam a recriacao como procedimento normal de atualizacao e de recuperacao.

```text
config.yaml:183:#   python pipeline.py --recreate
CONTEXTO_MELHORIA_RECUPERACAO_RAG.md:425:- para reconstruir integralmente a base, usar `python pipeline.py --recreate`.
CONTEXTO_MELHORIA_RECUPERACAO_RAG.md:427:No Pinecone, `--recreate` limpa somente o namespace configurado. Ele não apaga o índice físico `lead-media`.
CONTEXTO_MELHORIA_RECUPERACAO_RAG.md:437:5. reindexar com `python pipeline.py --recreate`;
README.md:65:uv run python pipeline.py --recreate
GUIA_DE_USO.md:488:Nao use `--recreate` na primeira carga de uma collection nova.
GUIA_DE_USO.md:519:- se documentos ou chunks forem removidos, use `--recreate` para eliminar registros antigos do namespace.
GUIA_DE_USO.md:543:python pipeline.py --recreate
GUIA_DE_USO.md:546:No Qdrant, `--recreate` apaga somente a collection configurada, cria-a novamente e indexa a versao atual dos documentos.
GUIA_DE_USO.md:548:No Pinecone, `--recreate` nao apaga o indice compartilhado. Ele limpa somente o namespace configurado e indexa a versao atual dos documentos.
GUIA_DE_USO.md:550:Nunca use `--recreate` sem conferir o nome da collection, pois os dados anteriores daquela collection serao apagados.
GUIA_DE_USO.md:634:Nao execute o pipeline comum novamente. Se a intencao for substituir toda a base, revise o nome e use `--recreate`.
GUIA_DE_USO.md:663:python pipeline.py --recreate
```

### GUIA_DE_USO.md linhas 515,522

```text
- `lead-media` e o indice fisico;
- `vivo_gold_banda_larga_pf` e o namespace isolado desta base;
- o indice e o embedding usam 1536 dimensoes;
- os IDs sao determinísticos, portanto repetir um upsert dos mesmos chunks atualiza os registros em vez de criar novas copias;
- se documentos ou chunks forem removidos, use `--recreate` para eliminar registros antigos do namespace.

 ## 10. Confirmar a indexacao

```

### GUIA_DE_USO.md linhas 630,637

```text
O helper atual do projeto converte HTTPS sem porta para a porta 443. Nao acrescente `:6333` ao endpoint publico.

 ### A collection ja possui pontos

Nao execute o pipeline comum novamente. Se a intencao for substituir toda a base, revise o nome e use `--recreate`.

 ### Os documentos nao aparecem

```

### CONTEXTO_MELHORIA_RECUPERACAO_RAG.md linhas 420,440

```text
Consequências:

- repetir o pipeline com os mesmos chunks atualiza os mesmos IDs;
- a repetição não cria cópias;
- se chunks forem removidos ou reordenados, podem permanecer registros antigos;
- para reconstruir integralmente a base, usar `python pipeline.py --recreate`.

No Pinecone, `--recreate` limpa somente o namespace configurado. Ele não apaga o índice físico `lead-media`.

 ## 15. Proposta em etapas

 ### Etapa 1 — correção imediata

1. manter o split em `#`, `##` e `###`;
2. adicionar um resumo consolidado ao documento de planos;
3. elevar `top_k` para 8 ou 10;
4. impedir exposição do JSON bruto da ferramenta;
5. reindexar com `python pipeline.py --recreate`;
6. testar perguntas gerais e específicas.

 ### Etapa 2 — melhoria estrutural
```
