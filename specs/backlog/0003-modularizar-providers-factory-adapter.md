# Backlog: Modularizar providers com Factory e Adapter

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0003 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Arquitetura de providers |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | `specs/defined/0003-modularizar-providers-factory-adapter/spec.md` |

## Ideia original

Separar providers de embeddings e bancos vetoriais do módulo monolítico atual usando contratos, Factory e Adapter, definindo o escopo oficial e a paridade esperada.

## Problema percebido

O `src/embedder.py` concentra condicionais e comportamentos de OpenAI, OpenRouter, Hugging Face, Qdrant, ChromaDB e Pinecone numa mesma função. Cerca de 130 linhas de sincronização (releitura de escopo lógico, upsert em lote, remoção de obsoletos, guarda de segurança) existem somente para o Qdrant, acopladas ao SDK do provider. Trocar de fornecedor — ou conectar um novo, como Postgres/pgvector — exige hoje reescrever esse núcleo. Além disso, cada backend se comporta de forma diferente escondida dentro do mesmo `if`: Qdrant faz sincronização idempotente completa com contagens estruturadas; ChromaDB faz `append` que duplica registros a cada execução; Pinecone faz `append` com IDs estáveis, sem remover obsoletos e sem contagens.

## Pessoa afetada ou beneficiada

Mantenedores do componente e equipe responsável pela integração futura no `rag-pipeline`.

## Resultado ou valor esperado

O sistema é o pipeline (chunking → embeddings → indexação → recuperação). Os bancos vetoriais e os providers de embeddings/LLM deixam de ser peças estruturais e passam a ser **plugins intercambiáveis** encaixados num soquete: contratos neutros de fornecedor + Factory + declaração de capacidade + suíte de conformidade + adapter de referência. Conectar Qdrant hoje, ou Postgres amanhã, ou outro provider de embeddings, passa a ser implementar o contrato + registrar na factory + adicionar a dependência — sem tocar no pipeline nem nos consumidores. A entrega desta fatia é o soquete, não os plugins específicos.

## Contexto

Item P1 do milestone M0. A pessoa responsável quer um sistema **plug and play** para toda família de provider — banco vetorial, embeddings, LLM. Começa operando com Qdrant + OpenAI; qualquer troca futura deve ser barata e não exigir mudança no pipeline. A regra de arquitetura confirmada (`.specsfy/RULES.md`) já exige Factory/Adapter para criação de providers e Strategy para comportamentos que variam por contexto.

Esta fatia estabelece o padrão plug and play e o aplica a **duas** famílias: embeddings e vector store. A família de LLM de chat/geração (`ChatOpenAI` hardcoded em `chat.py`) fica para BACKLOG-0010, aplicando o mesmo padrão. Elevar ChromaDB e Pinecone à superfície completa de `mirror` fica para BACKLOG-0009.

## Referências relacionadas

- `.specsfy/RULES.md` (Arquitetura, Operação) — Factory/Adapter para providers, Strategy por contexto; e a regra que exige registrar modo, escopo lógico e contagens `previstos/inseridos/mantidos/removidos` em **cada** execução de sincronização. Tipo: regra do projeto.
- `.specsfy/STACK.md` — providers implementados: OpenAI, OpenRouter e Hugging Face (embeddings); Qdrant, ChromaDB e Pinecone (vetoriais). Tipo: contexto de stack.
- `src/embedder.py` — implementação monolítica atual a ser substituída. Tipo: código de origem.
- `src/safety.py` — `SyncSafetyPolicy`, política fail-closed da SPEC-0001 que a base dos adapters deve invocar. Tipo: dependência de comportamento.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md` — SPEC-0001 concluída. NFR-001 (fail-closed antes de qualquer mutação), NFR-002 (contagens em cada execução), NFR-003 e "fora de escopo" **encaminharam a identidade estável / idempotência do ChromaDB a este backlog**; `mirror` permanece só no Qdrant (FR-005, FR-007). Tipo: spec relacionada (precedente).
- `specs/backlog/0004-remover-hardcodes-cliente.md` — hardcodes de cliente na configuração; complementar, fora do escopo desta fatia. Tipo: backlog relacionado.
- `specs/backlog/0007-gates-entrega-handoff.md` — dono da esteira de CI (Ruff + Pytest a cada push); esta fatia não cria o workflow. Tipo: backlog relacionado.
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md` — épico pai M0; os backlogs 0001–0007 são executados antes da consolidação no projeto-mãe. Tipo: backlog relacionado (pai).
- `specs/backlog/0009-paridade-mirror-chroma-pinecone.md` — leva `mirror` idempotente com remoção guardada de obsoletos a ChromaDB e Pinecone, sobre o contrato desta fatia. Tipo: backlog de acompanhamento.
- `specs/backlog/0010-provider-llm-plugavel.md` — aplica o padrão plug and play à família de LLM de chat/geração (`ChatOpenAI` em `chat.py`). Tipo: backlog de acompanhamento.
- Consumidores da fronteira atual: `search.py`, `chat.py`, `pipeline.py`, `upsert_from_chunks.py`, `demo_rag.py`; suítes `tests/test_safety.py` e `tests/test_qdrant_sync.py`. Tipo: superfície afetada.
- `.agents/skills/specsfy-specialist-langchain` — orienta a migração de imports LangChain da era v0 para v1; carregar ao desenhar os adapters. Tipo: especialista.
- Linear `LEAD-89` — tracking do item no milestone M0. Tipo: projeção de acompanhamento.

## Comportamento esperado

1. **Contratos neutros de fornecedor** para as duas famílias de provider (embeddings, vector store), declarados em `src/providers/contracts.py`. O contrato de vector store não expõe conceitos exclusivos de um backend (`collection`, `points`, `payload`, `scroll`, `namespace`, `index`); usa termos neutros (ex.: `ensure_ready(dimensions, metric)`, `upsert(records)`, `query(embedding, k, scope)`) e trata o escopo lógico validado (`project_id` obrigatório e `tenant_id` opcional) da SPEC-0001 como conceito do contrato. Ausência de `tenant_id` significa consultar somente registros sem tenant, nunca todos os tenants do mesmo projeto.
2. **Segregação de interface.** O contrato de vector store é `VectorStoreAdapter` (núcleo: `ensure_ready`, `list_ids(scope)`, `upsert`, `query` e emissão do log de contagens) + a extensão `MirrorCapableVectorStore` (`delete_ids(ids)` e remoção guardada de obsoletos). Todo adapter implementa o núcleo por inteiro e consegue reler os IDs do próprio escopo para calcular contagens exatas; só quem declara `mirror` implementa a extensão destrutiva. Não há método do núcleo "que não existe" em um adapter.
3. **Adapter de referência in-memory** implementa núcleo + extensão completos, sem nenhum SDK de banco. É a prova executável de que o contrato é neutro e a fixture da suíte de conformidade. Não é usado em produção.
4. **Fake determinístico de embeddings** (vetores estáveis, sem rede) para a suíte de conformidade da família de embeddings.
5. **Factory só despacha pelo nome do provider** lido do `config.yaml`. Nome desconhecido → `UnknownProviderError`. A factory não lê configuração detalhada nem segredos.
6. **Cada adapter valida os próprios settings localmente na inicialização:** resolve a configuração própria e as variáveis de ambiente aplicáveis (por exemplo, `index_name` do `config.yaml` com fallback em `PINECONE_INDEX`, além de segredos como `*_API_KEY`), lançando `InvalidProviderConfigError` para configuração incompleta e `MissingCredentialError` para credencial ausente — ambas subtipos de `ProviderError`, ambas sem chamada remota. Somente depois da validação do escopo, `ensure_ready` pode criar/acessar o cliente remoto e conferir condições do destino, como a dimensão do índice Pinecone. O fallback atual `index_name` de `config.yaml` **ou** `PINECONE_INDEX` é preservado.
7. Cada provider é um adapter isolado, em seu próprio módulo, sem condicionais por fornecedor fora da factory. Os adapters usam os pacotes LangChain v1 atuais (`langchain-huggingface`, `langchain-qdrant`) no lugar dos imports depreciados de `langchain_community`.
8. **Fail-closed uniforme.** A base de sincronização invoca `SyncSafetyPolicy.assert_sync_mode_supported` e `assert_valid_scope` **antes de instanciar o cliente remoto de qualquer adapter** — Qdrant, ChromaDB e Pinecone. Escopo ou modo inválido encerra em erro sem abrir conexão nem fazer upsert.
9. **Declaração de capacidade.** Cada adapter de vector store declara o que suporta. Núcleo: todos oferecem `append`, releitura dos IDs no escopo lógico e contagens exatas. `mirror` + remoção de obsoletos: somente Qdrant e in-memory. ChromaDB e Pinecone não removem obsoletos nesta fatia.
10. **Log de sincronização uniforme e exato.** Antes do upsert, os três backends consultam os IDs do próprio escopo lógico e registram modo, escopo e contagens numéricas exatas de `previstos/inseridos/mantidos/removidos`, cumprindo a regra de operação de `.specsfy/RULES.md` e a NFR-002 da SPEC-0001. Em `append`, `inseridos` conta apenas IDs ainda ausentes, `mantidos` conta IDs esperados já existentes e `removidos` é sempre `0`.
11. **Preservação de comportamento, com uma exceção encaminhada pela SPEC-0001.** Qdrant e Pinecone mantêm exatamente o que fazem hoje. Em destino ChromaDB novo/vazio, o upsert usa IDs estáveis (`chunk_id`) e deixa de duplicar registros a cada execução — mudança explicitamente encaminhada a este backlog pela SPEC-0001 (fora de escopo e NFR-003). Se forem detectados IDs legados incompatíveis, a escrita é bloqueada antes de qualquer mutação e o operador é orientado a configurar um destino vazio; esta fatia não migra nem remove a base antiga.
12. **`mirror` com remoção de obsoletos continua só no Qdrant**, guardado pela `SyncSafetyPolicy` exatamente como na SPEC-0001 (FR-005, FR-007). Levar isso a ChromaDB e Pinecone é BACKLOG-0009.
13. `src/embedder.py` deixa de existir; os cinco consumidores passam a usar a factory e os adapters diretamente, sem shim.
14. **Suíte de conformidade** roda: o contrato do núcleo contra **todos** os adapters de vector store, incluindo isolamento de `list_ids(scope)` e exatidão das contagens na primeira execução e na reexecução (nenhuma asserção do núcleo pulada); o contrato de `mirror` contra os que o declaram; os cenários fail-closed contra os três backends reais; o determinismo da família de embeddings contra o fake.
15. **Teste estático:** nenhum SDK de vector store nem classe de embeddings de provider é importado fora de `src/providers/`. O import direto de `ChatOpenAI` em `chat.py` permanece explicitamente permitido até o BACKLOG-0010, porque a família de LLM está fora desta fatia.
16. **Recuperação sempre escopada.** `search.py`, `chat.py` e `demo_rag.py` obtêm o `project_id` da configuração e aceitam `tenant_id` explícito quando aplicável. O escopo é validado antes de criar ou acessar qualquer cliente remoto; `project_id` ausente/vazio falha localmente. `tenant_id` ausente restringe a consulta aos registros sem tenant. Os consumidores usam apenas o contrato neutro e não montam filtros específicos de SDK.

## Regras de negócio

- **Providers são plugins, não estrutura.** Nenhum banco vetorial ou provider de embeddings é parte do sistema; todos são adapters intercambiáveis sobre o mesmo contrato. O pipeline e os consumidores dependem só do contrato.
- **Escopo oficial:** os três bancos vetoriais e os três providers de embeddings atuais são suportados contra o contrato. Nenhum é removido. Adicionar um novo (ex.: Postgres/pgvector) não pode exigir mudança no pipeline nem nos consumidores.
- **Contrato neutro de fornecedor:** o Port não expõe vocabulário exclusivo de um backend; cada adapter traduz para o seu SDK.
- **Segregação de interface:** núcleo `VectorStoreAdapter`, incluindo `list_ids(scope)` somente leitura, implementado por todos; extensão destrutiva `MirrorCapableVectorStore` só por quem declara `mirror`.
- **Fail-closed uniforme:** a `SyncSafetyPolicy` roda antes de qualquer criação de cliente ou mutação, para todos os backends. Nenhum caminho novo — inclusive caminhos de erro — executa mutação remota sem passar por ela.
- **Recuperação isolada por escopo:** toda busca exige `project_id`; `tenant_id`, quando fornecido, restringe o resultado ao tenant exato. Sem `tenant_id`, somente registros sem tenant podem ser retornados. Consulta inválida falha antes de acessar o provider.
- **Preservação da SPEC-0001:** a política permanece em `src/safety.py` como fonte central e é chamada pela base dos adapters.
- **Contagens exatas em cada execução:** os três backends relêem somente os IDs do próprio escopo antes do upsert e emitem o log estruturado (RULES.md, NFR-002). `mirror`/remoção de obsoletos permanece só no Qdrant nesta fatia.
- **ChromaDB ganha IDs estáveis:** única mudança de comportamento aceita, por encaminhamento explícito da SPEC-0001.
- **Fronteira de validação:** factory despacha pelo nome (`UnknownProviderError`); o adapter valida seus settings na init (`InvalidProviderConfigError`, `MissingCredentialError`), preservando o fallback `PINECONE_INDEX`. Mensagens em português que o operador vê hoje são preservadas no texto.
- **Fronteira interna:** não há consumidor externo. `src/embedder.py` é removido sem shim; os cinco scripts internos são migrados na mesma fatia.
- **Organização de módulos:** `src/providers/` com `contracts.py`, `factory.py`, `embeddings/` (`base.py`, `openai.py`, `openrouter.py`, `huggingface.py`, `fake.py`) e `vectorstores/` (`base.py`, `qdrant.py`, `chroma.py`, `pinecone.py`, `in_memory.py`).
- **Migração de imports LangChain:** adapters adotam `langchain-huggingface` e `langchain-qdrant`; as duas dependências entram no `pyproject.toml`. Comportamento observável (dimensões, distância, payload) preservado e verificado pela conformidade.
- **Desacoplamento verificável:** nenhum import de `qdrant_client`, `pinecone`, `langchain_chroma`, `langchain_pinecone`, `langchain_qdrant`, `langchain_huggingface` ou `langchain_community` para vector stores/embeddings, nem de `OpenAIEmbeddings`, aparece fora de `src/providers/`, checável por teste estático. `ChatOpenAI` em `chat.py` é a exceção temporária e rastreada pelo BACKLOG-0010.
- **Sem regressão para o operador:** `config.yaml` e o contrato de metadados dos chunks não mudam.
- **CI fora de escopo:** criar a esteira (Ruff + Pytest a cada push) é do BACKLOG-0007. Esta fatia garante Pytest verde e Ruff verde (quando configurado) localmente.

## Critérios de aceitação

```gherkin
Scenario: Preservar o comportamento de Qdrant e Pinecone
  Given o pipeline configurado para Qdrant ou para Pinecone
  When o operador executa indexação, busca e reexecução da mesma base
  Then o resultado observável é idêntico ao do ramo correspondente da
       implementação monolítica atual
  And para Qdrant isso inclui mirror, remoção de obsoletos e as contagens
      previstos/inseridos/mantidos/removidos

Scenario: ChromaDB deixa de duplicar registros
  Given um destino ChromaDB novo indexado pelo adapter com IDs estáveis
  When o operador executa novamente o mesmo pipeline sem alterar a entrada
  Then nenhum registro duplicado é criado, porque o upsert usa chunk_id
       como identidade estável
  And essa é a mudança de comportamento encaminhada pela SPEC-0001

Scenario: Base ChromaDB legada é preservada sem escrita
  Given um destino ChromaDB com registros cujos IDs não correspondem ao
        contrato estável
  When o operador inicia a sincronização
  Then a execução é bloqueada antes de qualquer upsert
  And a base legada permanece inalterada
  And a mensagem orienta configurar um destino novo e vazio

Scenario: Log de contagens uniforme nos três backends
  Given uma base sincronizada em Qdrant, ChromaDB ou Pinecone
  When o operador reexecuta a mesma entrada sem alterações
  Then ele contém modo, escopo lógico e as contagens
       previstos/inseridos/mantidos/removidos
  And inseridos é 0
  And mantidos é igual a previstos
  And removidos é 0 nos backends em append
  And não contém credenciais, tokens nem URL de destino

Scenario: Contrato neutro provado pelo adapter de referência
  Given o adapter de referência in-memory
  When a suíte de conformidade roda contra ele
  Then ele passa nas asserções do núcleo e da extensão mirror
  And nenhum import de SDK de banco é necessário para implementá-lo
  And o contrato não expõe collection, points, payload, scroll, namespace
      ou index como conceitos próprios

Scenario: O núcleo do contrato é o mesmo para todos os adapters
  Given todos os adapters de vector store
  When a suíte de conformidade roda o contrato do núcleo
  Then todos passam nas mesmas asserções de ensure_ready, list_ids por escopo,
       upsert, query e emissão de contagens exatas, sem asserção pulada
  And o contrato de mirror roda apenas contra Qdrant e in-memory

Scenario: Fail-closed antes de qualquer cliente ou upsert, nos três backends
  Given um provider entre Qdrant, ChromaDB e Pinecone
  And um escopo lógico inválido (project_id ausente ou divergente,
      chunk_id ausente ou duplicado, ou conjunto esperado vazio)
      ou um modo de sincronização incompatível
  When a sincronização é iniciada
  Then a SyncSafetyPolicy encerra a execução em erro
  And nenhum cliente remoto é criado e nenhum upsert é feito
  And o client falso registra lista vazia de mutações

Scenario: Recuperação isolada por projeto e tenant
  Given registros de dois tenants no mesmo project_id
  When search.py ou chat.py consulta com o project_id e um tenant_id explícito
  Then somente resultados desse par project_id e tenant_id são retornados
  And o consumidor não constrói filtros específicos do SDK

Scenario: Consulta sem tenant não atravessa tenants
  Given registros sem tenant e registros de tenants no mesmo project_id
  When uma consulta informa o project_id sem tenant_id
  Then somente registros sem tenant são retornados
  And registros de qualquer tenant ficam fora do resultado

Scenario: Consulta sem projeto falha localmente
  Given uma consulta sem project_id válido
  When o consumidor tenta iniciar a recuperação
  Then a execução termina com erro de escopo
  And nenhum cliente remoto é criado e nenhuma consulta é enviada

Scenario: Provider desconhecido falha na factory
  Given um nome de provider desconhecido no config.yaml
  When a factory tenta criar o provider
  Then lança UnknownProviderError com a mensagem atual
  And nenhuma configuração detalhada e nenhum segredo são lidos

Scenario: Config incompleta ou credencial ausente falha no adapter
  Given um adapter cuja configuração está incompleta ou cujo segredo
        obrigatório não está no ambiente
  When o adapter é inicializado
  Then lança InvalidProviderConfigError ou MissingCredentialError com a
       mensagem atual do provider
  And nenhuma chamada remota é feita
  And para Pinecone, index_name continua podendo vir de config.yaml
      ou da variável PINECONE_INDEX

Scenario: Corte limpo do módulo antigo
  Given o repositório após a modularização
  When se busca por src/embedder.py e por imports de src.embedder
  Then o módulo não existe
  And nenhum consumidor (search.py, chat.py, pipeline.py,
      upsert_from_chunks.py, demo_rag.py) o referencia
  And Pytest segue verde e Ruff segue verde quando configurado

Scenario: Imports LangChain atualizados e nenhum SDK vazando
  Given o código após a modularização
  When o teste estático varre imports fora de src/providers/
  Then nenhum módulo importa qdrant_client, pinecone, langchain_chroma,
       langchain_pinecone, langchain_qdrant, langchain_huggingface ou
       langchain_community para vector stores ou embeddings
  And nenhum módulo fora de src/providers/ importa OpenAIEmbeddings
  And os adapters usam langchain-huggingface e langchain-qdrant no lugar
      de langchain_community
  And o import de ChatOpenAI em chat.py permanece permitido até o BACKLOG-0010
```

## Qualidades e operação

- **Segurança:** a `SyncSafetyPolicy` da SPEC-0001 é preservada e centralizada; sincronização e recuperação validam o escopo antes de qualquer criação/acesso de cliente remoto, para os três backends. Consultas não atravessam `project_id` nem `tenant_id`. Nenhum segredo novo entra no repositório; credenciais são lidas apenas dentro dos adapters, nunca na factory.
- **Privacidade:** sem mudança — o componente não persiste dados pessoais próprios.
- **Desempenho e volume:** sem regressão. Processamento em lote (`batch_size`) e releitura paginada de escopo (Qdrant) preservados.
- **Auditoria e observabilidade:** log estruturado uniforme e exato nos três backends (modo, escopo, quatro contagens), calculado por releitura isolada dos IDs antes do upsert e sem expor segredos — cumpre RULES.md e NFR-002.
- **Testes:** suíte de conformidade como gate — núcleo contra todos os adapters, extensão `mirror` contra os que declaram, fail-closed contra os três backends, determinismo de embeddings contra o fake. Teste estático de desacoplamento de imports. Pytest verde localmente; Ruff verde quando configurado.
- **Dependências:** `langchain-huggingface` e `langchain-qdrant` entram no `pyproject.toml`.
- **Processo:** branch própria da fase; Red-Green-Refactor nos componentes críticos.

## Dependências

- **SPEC-0001 (BACKLOG-0001) — concluída.** Fornece a `SyncSafetyPolicy`; esta fatia a preserva, a chama na base dos adapters e cumpre o encaminhamento de ChromaDB.
- **BACKLOG-0004** — hardcodes de cliente na configuração; complementar, separado. Esta fatia não altera `config.yaml`.
- **BACKLOG-0007** — esteira de CI; esta fatia não a cria.
- **BACKLOG-0008 (épico pai)** — decomposição M0.
- **BACKLOG-0009 e BACKLOG-0010** — dependem do contrato e da suíte de conformidade entregues aqui; não bloqueiam esta fatia.
- Nenhuma dependência bloqueante pendente.

## Situações de erro

- **Provider desconhecido:** a factory lança `UnknownProviderError` com a mensagem atual (`Provedor de embeddings nao suportado` / `Vector store nao suportado`). Nada mais lido, nenhuma chamada remota.
- **Config incompleta:** ausência de `index_name`/`namespace` para Pinecone (após tentar o fallback `PINECONE_INDEX`), `QDRANT_URL` não HTTP(S) — o adapter lança `InvalidProviderConfigError` com as mensagens atuais, na inicialização.
- **Credencial ausente ou placeholder:** o adapter lança `MissingCredentialError` na inicialização, com a mensagem atual por provider (ex.: `OPENAI_API_KEY nao configurada no .env`). Nenhuma chamada remota.
- **Escopo lógico inválido ou modo incompatível:** a base chama a `SyncSafetyPolicy` antes de criar cliente; `InvalidSyncScopeError` / `UnsupportedSyncModeError`. `mirror` fora do Qdrant continua recusado. Vale para os três backends.
- **Conjunto esperado vazio / remoção não confirmada:** `UnsafeRemovalError`, comportamento inalterado (Qdrant).
- **Dimensão incompatível do índice:** mantida como hoje — após a validação local e do escopo, `ensure_ready` consulta o Pinecone e rejeita a dimensão divergente; o Qdrant dimensiona a collection na criação. Uniformizar é BACKLOG-0009.
- **Escopo de consulta ausente ou inválido:** `project_id` ausente/vazio falha localmente antes de criar/acessar cliente remoto. `tenant_id` ausente é um escopo válido, mas corresponde exclusivamente a registros sem tenant.
- **ChromaDB legado:** IDs incompatíveis com o contrato estável bloqueiam a sincronização antes do upsert; a mensagem orienta configurar uma collection ou `persist_directory` novo e vazio. Nenhum registro legado é removido, migrado ou reinterpretado.

## Escopo

- **Dentro:**
  - contratos (Ports) neutros para embeddings e vector stores, com `list_ids(scope)` somente leitura no núcleo, segregação da extensão destrutiva e capability flags;
  - factory que despacha pelo nome do provider sem tocar em segredo;
  - adapters isolados para os seis providers atuais, validando os próprios settings na init;
  - adapter de referência in-memory (núcleo + `mirror`) e fake determinístico de embeddings;
  - base de sincronização que chama a `SyncSafetyPolicy` antes de qualquer cliente/mutação, nos três backends;
  - consultas de `search.py`, `chat.py` e `demo_rag.py` obrigatoriamente escopadas por `project_id` e, quando aplicável, `tenant_id` explícito, com validação anterior ao acesso remoto;
  - IDs estáveis no upsert do ChromaDB (encaminhamento da SPEC-0001);
  - detecção fail-closed de ChromaDB legado, sem migração ou remoção;
  - releitura isolada dos IDs e log de contagens estruturadas exatas nos três backends;
  - hierarquia de exceções `ProviderError` com mensagens atuais preservadas;
  - suíte de conformidade (núcleo em todos, `mirror` nos declarados, fail-closed nos três, determinismo de embeddings);
  - teste estático de desacoplamento de imports;
  - migração dos cinco consumidores e remoção de `src/embedder.py`;
  - atualização das suítes `tests/test_safety.py` e `tests/test_qdrant_sync.py`;
  - migração dos imports LangChain legados para `langchain-huggingface` e `langchain-qdrant`.
- **Fora:**
  - `mirror`/remoção de obsoletos para ChromaDB e Pinecone (BACKLOG-0009);
  - migração, limpeza ou exclusão de registros ChromaDB legados;
  - provider plugável de LLM de chat/geração (BACKLOG-0010);
  - adapter real de Postgres/pgvector ou qualquer provider novo em produção;
  - remoção de hardcodes de cliente (BACKLOG-0004);
  - mudanças em `config.yaml` ou no contrato de metadados dos chunks;
  - criação da esteira de CI (BACKLOG-0007);
  - qualquer coisa de FastAPI, backend ou frontend do projeto-mãe.

## Dúvidas, decisões e riscos

- **Decisão (Perguntas 1–2):** escopo oficial = três bancos + três providers de embeddings contra o mesmo contrato; a suíte de conformidade faz parte da entrega.
- **Decisão (Pergunta 3):** corte limpo — migrar os cinco consumidores e remover `src/embedder.py`, sem shim.
- **Decisão (Pergunta 4):** organização em `src/providers/`; `SyncSafetyPolicy` permanece em `src/safety.py`.
- **Decisão (Pergunta 5, revisada):** a factory apenas despacha pelo nome do provider; cada adapter valida seus settings na inicialização. Corrige a formulação original ("factory é o único validador"), que quebrava o fallback `PINECONE_INDEX` de `src/embedder.py:23`.
- **Decisão (Pergunta 7):** qualidades = sem regressão + conformidade como gate + teste estático de desacoplamento.
- **Decisão (Pergunta 9):** migrar os imports LangChain legados nesta fatia; duas dependências novas no `pyproject.toml`.
- **Decisão (Pergunta 10):** modularização com preservação de comportamento por provider; o contrato declara a superfície completa e cada adapter declara suas capacidades.
- **Decisão (Pergunta 11):** contrato neutro de fornecedor + adapter de referência in-memory como prova executável de neutralidade.
- **Decisão (Pergunta 12):** o BACKLOG-0003 entrega, para ChromaDB e Pinecone, IDs estáveis (item a) e log de contagens uniforme (item b); `mirror` completo (item c) fica no BACKLOG-0009. Registra a supersessão parcial do encaminhamento da SPEC-0001: a identidade estável do ChromaDB é cumprida aqui; a semântica de espelho para os backends `append` foi realocada ao BACKLOG-0009.
- **Decisão (Pergunta 13):** o provider de LLM de chat/geração (`ChatOpenAI` em `chat.py`) fica fora desta fatia; vira BACKLOG-0010 com o mesmo padrão plug and play.
- **Decisão (Pergunta 14):** ChromaDB e Pinecone consultam previamente os IDs do escopo e produzem contagens exatas. `list_ids(scope)` passa a integrar o núcleo comum e somente `delete_ids(ids)` permanece na extensão `mirror`; a reexecução inalterada registra `inseridos=0`, `mantidos=previstos` e `removidos=0` em `append`.
- **Decisão (Pergunta 15):** todos os consumidores de recuperação exigem `project_id` e aceitam `tenant_id` explícito quando aplicável. Sem tenant, a consulta alcança somente registros sem tenant; escopo inválido falha antes do acesso remoto. `search.py`, `chat.py` e `demo_rag.py` são migrados para essa fronteira neutra.
- **Correção da 1ª revisão:** CI e Ruff não são gates ativos (não há `.github/workflows/`, Ruff não está no `pyproject.toml`). Ajustado para Pytest verde local + Ruff verde quando configurado.
- **Correção da 2ª revisão (P1a/b/c, P2):** o aceite não pode usar o monólito não uniforme como referência única; a fronteira de validação estava ambígua. Resolvido pelas decisões das Perguntas 10 e 5-revisada.
- **Correção da 3ª revisão:** (i) contradição com RULES.md/NFR-002 sobre contagens — resolvida trazendo o log uniforme para os três backends; (ii) contrato indefinido para adapters parciais — resolvido por segregação de interface; (iii) fail-closed só cobria Qdrant — resolvido com cenários para os três backends e a guarda na base antes de qualquer cliente; (iv) validação quebrava o fallback `PINECONE_INDEX` — resolvida pela Pergunta 5-revisada.
- **Correção da 4ª revisão:** a proibição ampla de `langchain_openai` contradizia a decisão de deixar a família de LLM fora desta fatia. O teste estático passa a proibir SDKs/classes de vector store e embeddings fora de `src/providers/`, mantendo `ChatOpenAI` em `chat.py` como exceção rastreada pelo BACKLOG-0010. Também foi eliminada a duplicação textual de `PINECONE_INDEX` na descrição da configuração.
- **Risco:** as suítes `test_safety.py` e `test_qdrant_sync.py` fazem `monkeypatch` de `embedder.get_embeddings`; serão reescritas para a nova fronteira sem perder cobertura da SPEC-0001.
- **Risco:** `_get_qdrant_client()` em `src/embedder.py:46-74` carrega contornos do `qdrant-client==1.10.1` (porta 6333 padrão em HTTPS, ausência de `check_compatibility`); o adapter Qdrant deve preservá-los ao adotar `langchain-qdrant`.
- **Risco:** a releitura prévia para contagens deve ser paginada e restrita ao escopo lógico em cada SDK; falha, paginação incompleta ou filtro não confiável bloqueia a sincronização em vez de produzir contagem aproximada ou consultar outro escopo.
- **Risco:** os três SDKs expressam ausência de `tenant_id` de formas diferentes. A suíte de conformidade deve provar que o filtro "sem tenant" não equivale a omitir o filtro e não retorna registros tenantizados.
- **Decisão (verificação local após a Pergunta 15):** não existe base ChromaDB local a migrar: o provider ativo em `config.yaml` é Qdrant, o caminho configurado `output/vivo_gold_banda_larga_pf/chroma_db` está ausente e não foi encontrado `chroma.sqlite3` no projeto fora da `.venv`. A garantia de IDs estáveis começa em destino Chroma novo/vazio. Se uma base legada surgir, a sincronização bloqueia antes da escrita e orienta outro destino; migração/limpeza fica fora do escopo.
- **Sugestão de Effort para a spec:** 7 (`high`) — refatoração ampla em caminho crítico de segurança; ~13 módulos novos (inclui in-memory e fake); cinco consumidores migrados; duas suítes reescritas mais a de conformidade; migração de dois pacotes LangChain; contrato neutro com segregação de interface. Os itens (a)+(b) para ChromaDB/Pinecone são pequenos e cabem no 7.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** o `src/embedder.py` monolítico acopla o pipeline a SDKs de fornecedores e esconde comportamentos divergentes de três bancos na mesma função. Objetivo: um soquete plug and play — contratos neutros + Factory + Adapter + conformidade — para as famílias de embeddings e vector store, de modo que trocar ou adicionar provider (incl. Postgres/pgvector) não toque no pipeline. Começa com Qdrant + OpenAI.
2. **Atores:** mantenedores do componente; equipe da integração futura no `rag-pipeline`. Sem interface para pessoas.
3. **Escopo:** contratos neutros com `list_ids(scope)` no núcleo, segregação da extensão destrutiva `mirror` e capability flags; factory que só despacha; seis adapters que validam os próprios settings; adapter in-memory e fake de embeddings; base que chama a `SyncSafetyPolicy` antes de qualquer cliente nos três backends; IDs estáveis no ChromaDB (SPEC-0001); contagens exatas nos três por releitura isolada do escopo; recuperação obrigatoriamente isolada por `project_id`/`tenant_id`; suíte de conformidade; teste estático; migração dos cinco consumidores e remoção de `src/embedder.py`; migração LangChain v1. Fora: `mirror` para ChromaDB/Pinecone (0009), LLM plugável (0010), adapter real de Postgres, hardcodes (0004), `config.yaml`/metadados, CI (0007), projeto-mãe.
4. **Jornadas e regras essenciais:** factory despacha pelo nome; adapter valida settings localmente; escopo é validado antes de `ensure_ready` ou `query`; a base aplica a política fail-closed antes de mutação, para todos os backends; recuperação nunca atravessa projeto/tenant; providers são plugins intercambiáveis; nenhum SDK de provider fora de `src/providers/`.
5. **Critérios de aceite (Given/When/Then):** preservação de Qdrant/Pinecone; ChromaDB sem duplicar; log uniforme e exato nos três; contrato neutro provado pelo in-memory; núcleo idêntico para todos os adapters; fail-closed nos três backends antes de cliente/upsert; recuperação isolada por projeto/tenant e falha local sem projeto; provider desconhecido na factory; config/credencial no adapter com fallback `PINECONE_INDEX` preservado; corte limpo; imports LangChain v1 sem SDK vazando. (Gherkin acima.)
6. **Restrições técnicas e de qualidade:** Python 3.12+/uv/LangChain v1; OO com Factory/Adapter/Strategy; `SyncSafetyPolicy` central preservada; adapters em pacotes LangChain v1; Pytest verde local e Ruff verde quando configurado (CI é do 0007); sem segredos novos; `config.yaml` e metadados inalterados; Red-Green-Refactor.
7. **Suposições:** não há consumidor externo da fronteira atual; `config.yaml` e o contrato de metadados dos chunks permanecem estáveis; ChromaDB, Pinecone e futuros backends são opções plugáveis, não alvo de operação; Qdrant + OpenAI são o alvo inicial.
8. **Decisões abertas:** nenhuma lacuna aplicável nesta fatia. A elevação de ChromaDB/Pinecone a `mirror` é BACKLOG-0009; o provider plugável de LLM é BACKLOG-0010; ambos criados como stub `Captured`.
9. **Vocabulário e inferências confirmadas:** "plug and play" = qualquer provider entra implementando o contrato + registrando na factory + adicionando a dependência, sem tocar no pipeline; "provider é plugin, não estrutura" = o sistema é o pipeline, os bancos e modelos são opções; "contrato neutro" = Port sem conceitos exclusivos de um backend; "segregação de interface" = núcleo obrigatório + extensão `mirror` opcional; "capability flag" = declaração explícita do adapter; "corte limpo" = sem shim.

## Próximo passo

BACKLOG-0009 e BACKLOG-0010 foram criados como stubs `Captured`. A fonte normativa está em `specs/defined/0003-modularizar-providers-factory-adapter/spec.md`; decisões futuras pertencem à spec.
