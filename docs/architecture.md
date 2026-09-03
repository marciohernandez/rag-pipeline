# Arquitetura

<!-- specsfy:documentator:start -->
## Componentes

| Tipo | Quantidade |
| --- | --- |
| Código | 0 |
| Testes | 0 |

## Diagramas

```mermaid
flowchart TD
  Application[Aplicação]
```

```mermaid
classDiagram
  class Application
```
<!-- specsfy:documentator:end -->

## Contrato da fronteira entre aplicação e pipeline

O pacote `src/app/` é o destino da camada de aplicação. Ele pode depender
somente da fachada síncrona em `src/pipeline/service.py`; importar qualquer
outro módulo de `src/pipeline/` é uma violação verificada por AST em
`tests/test_application_boundaries.py`. A dependência inversa também é
proibida: o pipeline não importa `src.app`.

A fachada recebe por parâmetro um dicionário de configuração não sensível já
resolvido. Ela não abre `config.yaml`, não consulta o ambiente para essa
configuração e não recebe credenciais em suas assinaturas. A resolução de
credenciais continua encapsulada nos providers. As operações são síncronas e
bloqueiam a thread chamadora; uma camada HTTP ou de jobs deverá executá-las fora
da thread de requisição quando precisar de assincronia.

| Operação pública | Entrada principal | Resultado |
| --- | --- | --- |
| `run_pipeline` | configuração, diretório de entrada opcional e modo somente chunks | documentos, chunks, manifesto, relatório de qualidade e contagens opcionais |
| `sync_vector_store` | configuração e sequência de chunks | `SyncCounts` com `previstos`, `inseridos`, `mantidos` e `removidos` |
| `validate_retrieval` | configuração e `tenant_id` opcional | `ValidationReport` com veredito, conferência e consultas |
| `query_base` | configuração, consulta, `top_k` e `tenant_id` opcional | resultados neutros com conteúdo, metadados e score |

Os adaptadores de linha de comando permanecem na raiz e continuam responsáveis
por resolver `config.yaml`: `pipeline.py`, `search.py`, `chat.py`, `validate.py`
e `upsert_from_chunks.py`. Eles preservam os argumentos existentes e delegam à
operação correspondente da fachada.

### Limites e dívidas bloqueantes

- `BACKLOG-0012` é bloqueante para iniciar implementação dentro de `src/app/`:
  a carga do ambiente ainda ocorre no import de `src/pipeline/config.py`.
- `BACKLOG-0013` é bloqueante para incorporar o backend de aplicação: o
  comportamento dos backends reais de vector store ainda precisa de cobertura
  própria.
- Prosseguir com a fatia de backend enquanto qualquer uma dessas dívidas
  estiver aberta exige reabrir a SPEC-0008; esta entrega cria apenas a
  fronteira interna.

### Baseline de regressão

A migração usa como baseline mínima os 238 testes registrados na definição da
SPEC-0008. Antes da mudança, a suíte já tinha evoluído para 239 testes
preexistentes aprovados; a entrega não pode reduzir essa contagem e deve manter
`uv run ruff check .` sem achados.

## Arquitetura Python verificada

```mermaid
flowchart LR
  Markdown[Markdown + frontmatter] --> Loader[src.pipeline.loader]
  Loader --> StatusGate[src.pipeline.status_gate]
  StatusGate --> Chunker[src.pipeline.chunker]
  Chunker --> Identity[src.pipeline.identity]
  Identity --> Manifest[src.pipeline.manifest]
  Identity --> Exporter[chunks.json]
  Manifest --> Quality[src.pipeline.quality]
  Quality --> Indexer[src.pipeline.embedder]
  Safety[src.pipeline.safety] --> Indexer
  Indexer --> Qdrant[(Qdrant)]
  Indexer --> Chroma[(ChromaDB)]
  Indexer --> Pinecone[(Pinecone)]
  Qdrant --> Search[search.py / chat.py]
```

O pipeline é uma aplicação CLI modular em Python. `pipeline.py` compõe os
módulos; desde a SPEC-0003 a criação de providers e o acesso à persistência
vivem em `src/pipeline/providers/`, atrás de contratos neutros e de uma factory, e
`src/pipeline/indexing.py` traduz `config.yaml` e chunks para esses contratos. O antigo
`src/pipeline/embedder.py`, lacuna registrada no BACKLOG-0003, foi removido.
Identidades determinísticas e manifesto sustentam idempotência e auditoria. O Qdrant implementa upsert antes da remoção
de obsoletos no mesmo `project_id`.

`src/pipeline/quality.py`, introduzido pela SPEC-0006, acrescenta um segundo ponto de
bloqueio entre o manifesto e a indexação. Ele separa invariante determinístico,
que interrompe a execução, de sinal heurístico, que apenas entra no relatório;
somente o primeiro pode reprovar uma carga. O módulo é leitura pura e não
importa SDK de banco vetorial.

`src/pipeline/safety.py` concentra a política fail-closed exigida antes de qualquer
mutação remota. `SyncSafetyPolicy` rejeita a opção `--recreate`, valida provider
e modo de sincronização, exige um único `project_id` sem `chunk_id` duplicado e
libera a remoção somente quando o destino confirma todos os pontos esperados.
Os entrypoints `pipeline.py` e `upsert_from_chunks.py` aplicam a guarda antes de
criar qualquer cliente.

`src/pipeline/validation.py` estabelece a fronteira local da validação de recuperação:
ele lê e valida o gabarito versionado antes de compor ou consultar um adapter e,
só então, executa o preflight de ambiente — existência do escopo e dimensão
declarada pelo destino — por leitura pura, sem preparar a coleção. Aprovado o
preflight, ele resolve o manifesto pela mesma regra de `pipeline.py`, confirma
que ele descreve a base configurada e compara por igualdade estrita os
`chunk_id` previstos com os devolvidos por `list_ids`, separando faltantes de
órfãos. Por fim executa o gabarito da base, avaliando cada consulta pela
categoria declarada: ampla e específica pelos fatos de `deve_conter` e pelo
`documento_esperado`, e sem resposta pela ausência de resultado que alcance
`validacao.limiar_minimo`. O roteiro roda mesmo com a conferência divergente,
porque é leitura pura e o operador precisa do quadro completo. O resultado sai
em duas formas: um relatório legível na ordem em que a validação acontece e um
JSON em `output/<base>/validation-<run_id>.json`, com preflight, conferência,
consultas e desfecho, sem credencial, token ou URL de destino. O caminho do
arquivo fica fora do JSON de propósito, para que o gravado seja idêntico ao que
o módulo devolve a quem o chama sem a linha de comando.

Para conferir o destino sem alterá-lo, o contrato neutro expõe
`VectorStoreAdapter.describe_scope(scope)`, acrescentado pela SPEC-0004. A
operação é leitura pura: devolve existência e dimensão declaradas pelo destino,
ou um mapa vazio quando o escopo não existe. Ela existe porque `ensure_ready`
prepara o destino e cria a coleção ausente, o que uma validação somente leitura
não pode fazer. Cada backend a implementa com a leitura própria do seu SDK —
`get_collection` no Qdrant, cliente direto do ChromaDB em vez do construtor que
faz get-or-create, `describe_index` no Pinecone — e o backend em memória serve
de referência.

O contrato de recepção de Markdown do projeto-mãe (SPEC-0002) estende esse
desenho em quatro pontos: `document_id` do frontmatter tem precedência sobre a
identidade determinística (`src/pipeline/identity.py`); `SyncSafetyPolicy.assert_valid_scope`
passou a validar e retornar também `tenant_id`, estendendo o escopo lógico
fail-closed para `project_id + tenant_id`; `src/pipeline/status_gate.py` exclui, antes
do chunking, documentos com `status` presente em uma lista bloqueante
configurável (`contrato_markdown.status_bloqueado` em `config.yaml`); e
`src/pipeline/chunker.py` ganhou o splitter `qa`, que divide o corpo por `++++` em um
chunk por bloco quando o documento declara `splitter: qa` no frontmatter.
`type` e `version` do frontmatter são propagados a cada chunk pelo mecanismo
de mesclagem de metadata já existente, sem efeito no processamento.
