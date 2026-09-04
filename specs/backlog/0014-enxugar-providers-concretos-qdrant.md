# Backlog: Enxugar providers concretos para Qdrant, mantendo o contrato multi-provider aberto

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0014 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-04 |
| Refinado em | 2026-09-04 |
| Spec promovida | `specs/draft/0010-enxugar-providers-concretos-qdrant/spec.md` (SPEC-0010) em 2026-09-04 |

## Ideia original

Manter só o Qdrant como implementação concreta de vector store. ChromaDB e
Pinecone saem do projeto (adapters, SDKs, ramos de factory, conformance
específica), mas o contrato neutro, o backend port e a `ProviderFactory`
continuam extensíveis, com `in_memory` como oráculo de referência. Providers
futuros voltam por novo adapter + registro, sem redesenho.

## Problema percebido

O projeto carrega três implementações concretas (Qdrant, ChromaDB, Pinecone),
seus SDKs e suítes de conformidade, mas só Qdrant está escolhido. Chroma e
Pinecone são superfície não usada: dependências instaladas, código sem
exercício real, defaults apontando para `"chroma"` e ruído de manutenção e de
teste (base do BACKLOG-0013).

## Pessoa afetada ou beneficiada

Quem mantém o pipeline (menos dependências e superfície) e quem for integrá-lo a
`src/app/` (fronteira menor, sem tradução de SDK não exercida).

## Resultado ou valor esperado

Projeto Qdrant-only na prática, com o contrato multi-provider preservado e
documentado como ponto de extensão. Pedir um provider removido levanta
`UnknownProviderError` com as opções restantes; suíte e `ruff` verdes com nova
baseline de regressão registrada.

## Contexto

Decisão tomada no refinamento do BACKLOG-0013 (2026-09-04): o usuário quer usar
multi-provider e manter o projeto aberto para isso, mas ainda não quer definir
quais providers além do Qdrant. Este item foi priorizado **antes** do
BACKLOG-0013 para que a cobertura de backend real não escreva teste para código
que será removido.

## Referências relacionadas

- `specs/backlog/0013-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`:
  item dependente; seu escopo foi reduzido a Qdrant-only por causa desta fatia.
  Tipo: backlog relacionado.
- `specs/completed/0003-modularizar-providers-factory-adapter/spec.md`: entregou
  o contrato neutro, o backend port, a `ProviderFactory` e os adapters
  concretos. Tipo: spec relacionada (limita o que pode ser removido).
- `specs/completed/0004-validar-recuperacao-operacao/spec.md`: cobriu `describe`
  dos backends reais em `tests/test_describe_scope_backends.py`; os casos de
  Chroma e Pinecone desse arquivo saem nesta fatia. Tipo: spec relacionada.
- `specs/completed/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md`:
  precedente de registro de baseline de regressão em `docs/architecture.md`.
  Tipo: spec relacionada.

## Comportamento esperado

- A `ProviderFactory` continua despachando por nome; adicionar um provider
  futuro passa a ser: novo `src/pipeline/providers/vectorstores/<nome>.py` +
  entrada em `_VECTOR_STORES` + parametrizar a suíte de conformidade.
- `ProviderFactory.create_vector_store("chroma")` e `"pinecone"` levantam
  `UnknownProviderError`, com a mensagem listando apenas as opções restantes
  (`qdrant`, `in_memory`).
- `InMemoryVectorStoreAdapter` permanece como adapter de referência do contrato.
- O caminho padrão de indexação sem `vector_store.provider` na config usa
  `qdrant`.
- O modo `mirror` continua exclusivo do Qdrant via `MirrorMixin`, sem mudança.

## Regras de negócio

- A abstração multi-provider (contrato neutro, backend port, `ProviderFactory`)
  é preservada e não pode ser simplificada nesta fatia.
- Só implementações concretas ainda não escolhidas são removidas: hoje, Chroma e
  Pinecone. Qdrant e `in_memory` permanecem.
- Nenhuma mudança no comportamento do Qdrant.

## Critérios de aceitação

- **AC-01** — Dado o registro de vector stores, Quando a factory é consultada,
  Então `chroma` e `pinecone` não constam e `create_vector_store("chroma")`
  levanta `UnknownProviderError`.
- **AC-02** — Dado o repositório após a fatia, Quando se busca por `chromadb`,
  `langchain-chroma`, `pinecone`, `ChromaVectorStoreAdapter` ou
  `PineconeVectorStoreAdapter`, Então não há ocorrência em `src/` (exceto
  artefatos gerados em `src/chunk.egg-info/`), `tests/` nem `pyproject.toml`.
- **AC-03** — Dado o caminho padrão de indexação sem `provider` na config,
  Quando o pipeline roda, Então usa `qdrant` e não falha por provider
  desconhecido.
- **AC-04** — Dada a suíte completa, Quando `uv run pytest` e
  `uv run ruff check .` rodam, Então tudo passa e a nova baseline de contagem
  está registrada em `docs/architecture.md`.
- **AC-05** — Dada a suíte de conformidade do contrato neutro, Quando executa,
  Então exercita `in_memory` e `qdrant` e prova as cinco operações do port.

## Qualidades e operação

- Segurança: sem impacto — nenhuma credencial nova; remove leitura de
  `CHROMA_*`/`PINECONE_*` apenas se aparecer como código morto.
- Privacidade: sem impacto.
- Desempenho e volume: sem impacto de runtime; reduz árvore de dependências e
  tempo de instalação/CI.
- Auditoria e observabilidade: sem impacto; logs do serviço de sincronização
  permanecem.

## Dependências

- Bloqueia o BACKLOG-0013 (deve ser especificado e entregue antes).
- Depende do contrato e adapters entregues pela SPEC-0003 (não pode quebrá-los).

## Situações de erro

- Config com `vector_store.provider: "chroma"` ou `"pinecone"` após a fatia:
  `UnknownProviderError` com as opções restantes, sem stack trace de import.
- CLI `upsert_from_chunks.py` recebendo `--provider chroma`: rejeitado pelo
  `choices` reduzido a `["qdrant"]`.

## Escopo

- **Dentro:**
  - remover `src/pipeline/providers/vectorstores/chroma.py` e `pinecone.py`;
  - tirar os ramos `"chroma"`/`"pinecone"` de `factory._VECTOR_STORES`,
    `base._REAL_PROVIDERS` e `safety._SUPPORTED_PROVIDERS`;
  - remover `chromadb`, `langchain-chroma` e `pinecone` de `pyproject.toml`;
  - trocar o default `provider="chroma"` → `"qdrant"` em `indexing.py` e
    `pipeline.py`;
  - reduzir `choices` do CLI `upsert_from_chunks.py` para `["qdrant"]`;
  - neutralizar as strings de path `./output/chroma_db` em `pipeline.py` e
    `demo_rag.py`;
  - reduzir a conformance parametrizada
    (`test_vectorstore_conformance.py`, `test_describe_scope_conformance.py`,
    `test_characterization_providers.py`) para `in_memory` + `qdrant`;
  - remover os casos de `describe` de Chroma/Pinecone em
    `test_describe_scope_backends.py`;
  - atualizar `.specsfy/STACK.md`, `.specsfy/PACKAGES.md` e
    `docs/architecture.md` (incl. nova baseline de regressão).
- **Fora:**
  - escolher ou adicionar novos providers;
  - redesenhar o contrato, o port ou a factory;
  - qualquer mudança no comportamento do Qdrant;
  - limpeza ampla de texto de ajuda e exemplos além dos defaults citados.

## Dúvidas, decisões e riscos

- **Decisão (2026-09-04):** "tirar do projeto" = remover as implementações
  concretas e dependências, **não** a abstração multi-provider.
- **Decisão (2026-09-04):** `provider` default vira `"qdrant"`.
- **Risco:** esquecer uma referência a Chroma/Pinecone e deixar código morto;
  mitigado pelo AC-02 como varredura estática.
- **Suposição:** `src/chunk.egg-info/*` é artefato gerado e não conta como
  ocorrência.
- **Suposição:** nenhum consumidor externo ao repositório depende hoje dos
  adapters Chroma/Pinecone.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promover com `$specsfy-03-specify`.
