# Auditoria: contrato de recepção de Markdown implementado hoje

Trechos literais consultados no commit `2d7c614`, lidos em 2026-09-01.
Licença: código e documentação próprios do projeto; cópia integral
permitida. Propósito: preservar o estado auditado do contrato de
`document_id`, `tenant_id`, `status`, `version`, `type` e do parsing de
frontmatter, já que a implementação da SPEC-0002 altera justamente esses
trechos.

## src/identity.py — sobrescrita incondicional de document_id

```python
def assign_document_identity(document: Document, project_id: str) -> None:
    """Inclui identidade e fingerprint da fonte no metadata do documento."""
    source_path = document.metadata.get("caminho_relativo") or document.metadata.get(
        "nome_arquivo", "desconhecido"
    )
    document.metadata["project_id"] = project_id
    document.metadata["document_id"] = stable_uuid("document", project_id, source_path)
    document.metadata.setdefault("source_hash", content_hash(document.page_content))
```

`assign_chunk_identities` compõe `base_key` a partir de
`(project_id, document_id, source_hash, chunk_type, logical_path, digest)` e
gera `chunk_id = stable_uuid("chunk", base_key, occurrence)` — qualquer
mudança na origem de `document_id` muda todos os `chunk_id` do documento.

## src/loader.py — colisão do parser de frontmatter com `---`

```python
def _parse_frontmatter(content: str) -> tuple[dict, str]:
    content = content.lstrip('﻿')
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)

    if match:
        raw_yaml = match.group(1)
        body = content[match.end():]
        ...
```

Um documento cujo corpo começa com `---` (formato Q&A separado por `---`) tem
o primeiro bloco engolido como se fosse YAML e removido do `page_content`.

## src/chunker.py — nenhum splitter reconhece `---`/`++++`

```python
def _split_by_characters(doc, chunk_size, chunk_overlap) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.create_documents([doc.page_content], metadatas=[doc.metadata])
```

`_get_splitter_config` já lê `doc_metadata.get("splitter")` por documento
(precedência sobre `config.yaml`), mecanismo reaproveitado pela SPEC-0002
para `splitter: qa`.

## src/safety.py — escopo lógico sem tenant_id

```python
def assert_valid_scope(self, chunks: Sequence[Any]) -> str:
    ...
    project_ids: set[str] = set()
    chunk_ids: list[str] = []
    for chunk in chunks:
        metadata = getattr(chunk, "metadata", None)
        ...
        project_id = self._clean_identifier(metadata.get("project_id"))
        chunk_id = self._clean_identifier(metadata.get("chunk_id"))
        ...
        project_ids.add(project_id)
        chunk_ids.append(chunk_id)

    if len(project_ids) != 1:
        raise InvalidSyncScopeError(...)
    ...
    return next(iter(project_ids))
```

Somente `project_id` e `chunk_id` são validados; `tenant_id` não existe no
vocabulário desta guarda.

## src/embedder.py — filtro Qdrant restrito a project_id

```python
project_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.project_id",
            match=MatchValue(value=project_id),
        )
    ]
)
```

Usado tanto na leitura (`scope_ids`) quanto na remoção de obsoletos em modo
espelho — nenhum filtro por `tenant_id` existe hoje.

## Base real sem frontmatter

```text
$ ls documentos/vivo_gold_banda_larga_pf/
Benefícios Banda Larga PF.md
Complemento Consolidado da Oferta Vivo Fibra.md
Oferta Vivo Fibra com SVA.md
regulamento-cinemark-vivo-valoriza-2025.md
regulamento_regras_das_categorias_de_clientes_vivo_beneficios_v6_20241213.md
Termos e condições da assinatura.md
vivo_fibra_pf_julho_2026.md
```

Nenhum desses sete arquivos tem frontmatter YAML — confirma a restrição de
compatibilidade retroativa (NFR-002) usada em todo o Ato I.
