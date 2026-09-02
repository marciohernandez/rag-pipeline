# Backlog: Validar recuperação e operação de ponta a ponta

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0006 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Validação operacional da recuperação |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-08-31 |
| Refinado em | 2026-09-01 |
| Spec promovida | `specs/draft/0004-validar-recuperacao-operacao/spec.md` |

## Ideia original

Adicionar preflight somente leitura, conferência de manifesto e contagens e um roteiro verificável de consultas amplas, específicas e sem resposta.

## Problema percebido

A idempotência local foi comprovada, mas a recuperação remota e as garantias operacionais ainda não possuem validação completa e repetível.

## Pessoa afetada ou beneficiada

Operadores responsáveis por aprovar uma base antes do consumo por aplicações RAG.

## Resultado ou valor esperado

A equipe consegue provar conexão, consistência da indexação e comportamento de recuperação sem realizar mutações destrutivas.

## Contexto

Item P1 do milestone M01; nenhuma operação remota foi executada durante a
auditoria de segurança. A SPEC-0003 substituiu toda a camada de providers, e as
141 asserções da suíte rodam contra clientes falsos: nenhuma execução real
contra Qdrant e OpenAI aconteceu depois da remoção de `src/embedder.py`. O
BACKLOG-0008 declara este item como dependência para comprovar a recuperação
antes da demonstração com front.

## Referências relacionadas

- `search.py`, `chat.py` e `scripts/check_qdrant_connection.py`: ferramentas de recuperação e diagnóstico atuais.
- `src/manifest.py`: contagens e identidades esperadas; `build_manifest` já grava `chunk_ids`, `chunk_count`, `chunk_type_counts` e `documents`.
- `src/providers/contracts.py`: `list_ids(scope) -> set[str]` e `query(scope, embedding, k)` no contrato núcleo de todo adapter; `SearchResult.score` é nativo de cada provider.
- `src/indexing.py`: `retrieve()` já recupera com escopo de projeto e tenant explícitos.
- `GUIA_DE_USO.md` e `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`: roteiros históricos de validação; a seção 13 esboça o formato das consultas de referência adotado por D3.
- BACKLOG-0001: precondição de segurança para qualquer verificação remota.
- BACKLOG-0004: origem dos hardcodes de cliente presentes nos dois protótipos removidos por D7.
- BACKLOG-0007: consumidor do resultado; precisa distinguir base divergente de ambiente indisponível.
- BACKLOG-0008: declara este item como dependência para a demonstração com front.
- `.specsfy/RULES.md`, seção Operação: regra confirmada sobre o registro de
  modo, escopo lógico e contagens por execução.
- `docs/testing.md`: runner, comando reproduzível e cobertura atual da suíte.
- `specs/completed/0003-modularizar-providers-factory-adapter/spec.md`: contratos neutros, fail-closed e NFR-003 que esta validação preserva.
- Linear `LEAD-91`: tracking do item no milestone M01.

## Comportamento esperado

1. O operador executa um comando único de validação apontando para o
   `config.yaml` da base.
2. O comando conclui toda a validação local antes de qualquer acesso remoto.
3. O preflight confere conexão autenticada, existência do escopo no destino e
   compatibilidade de dimensão com `embedding.dimensions`.
4. A conferência compara o conjunto de `chunk_id` do manifesto com o conjunto
   devolvido por `list_ids` no escopo, separando faltantes de órfãos.
5. O roteiro executa cada consulta do gabarito da base e avalia o resultado
   conforme a categoria declarada: ampla, específica ou sem resposta.
6. O comando imprime um relatório legível e grava o resultado estruturado em
   `output/<base>/validation-<run_id>.json`.
7. O comando encerra com `0` aprovado, `1` reprovado ou `2` não foi possível
   validar.

## Regras de negócio

- **D1**: a entrega é um comando CLI único, somente leitura, cuja lógica fica em
  módulo Python reaproveitável pelo backend FastAPI do BACKLOG-0008.
- **D2**: a conferência exige igualdade estrita entre os conjuntos de
  `chunk_id`; o relatório separa faltantes de órfãos.
- **D3**: o gabarito é versionado por base, no formato esboçado na seção 13 de
  `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`, com `pergunta`, `deve_conter`,
  `documento_esperado` e a categoria declarada em cada entrada.
- **D4**: a saída é dupla — relatório legível no stdout e JSON em
  `output/<base>/validation-<run_id>.json`, que é local e não versionado.
- **D5**: os desfechos são `0` aprovado, `1` reprovado após validar de fato e
  `2` quando não foi possível validar.
- **D6**: toda a entrada vem do `config.yaml`: `caminhos.consultas_referencia`
  localiza o gabarito, o escopo lógico sai de `projeto.nome` e `--tenant` é
  opcional. Nenhum identificador de cliente no código.
- **D7**: `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`
  são removidos nesta fatia, depois que o comando cobrir preflight e consulta.
- **D8**: uma consulta da categoria sem resposta passa quando nenhum resultado
  atinge `validacao.limiar_minimo` declarado no config da base.
- A validação nunca escreve: nenhum caminho envia upsert ou remoção ao destino.
- O acesso ao destino ocorre exclusivamente pelos contratos de `src/providers/`.

## Critérios de aceitação

```gherkin
Scenario: Base íntegra é aprovada
  Given um manifesto e um destino com exatamente os mesmos chunk_ids
  And um gabarito cujas consultas retornam os fatos e documentos declarados
  When o operador executa a validação
  Then o relatório aprova a base e o comando encerra com código 0

Scenario: Indexação parcial reprova
  Given um destino sem parte dos chunk_ids do manifesto
  When o operador executa a validação
  Then o relatório lista os faltantes e o comando encerra com código 1

Scenario: Resíduo de execução antiga reprova
  Given um escopo com chunk_ids ausentes do manifesto
  When o operador executa a validação
  Then o relatório lista os órfãos e o comando encerra com código 1

Scenario: Consulta específica sem a fonte esperada reprova
  Given uma consulta do gabarito que declara documento_esperado
  When esse documento não aparece entre os top-k recuperados
  Then a consulta é marcada como reprovada e o comando encerra com código 1

Scenario: Consulta sem resposta que responde reprova
  Given uma consulta declarada na categoria sem resposta
  When algum resultado atinge o limiar mínimo da base
  Then a consulta é marcada como reprovada e o comando encerra com código 1

Scenario: Ambiente indisponível não é reprovação
  Given credencial ausente, escopo inexistente ou dimensão divergente
  When a validação é iniciada
  Then o comando encerra com código 2 sem executar consulta alguma

Scenario: A validação nunca escreve
  When qualquer caminho da validação executa, inclusive os de falha
  Then nenhuma operação de upsert ou remoção é enviada ao destino

Scenario: O registro não vaza segredo
  When o relatório e o JSON de resultado são produzidos
  Then nenhum deles contém credenciais, tokens ou URL de destino
```

## Qualidades e operação

- Segurança: acesso somente leitura, sem qualquer mutação no destino; o acesso
  ocorre pelos contratos neutros de `src/providers/`, preservando o NFR-003 da
  SPEC-0003; a validação local precede todo acesso remoto, herdando o
  fail-closed já estabelecido.
- Privacidade: o gabarito fica ao lado dos documentos da base, que já são
  versionados no repositório; nenhuma exposição nova é criada. Credenciais,
  tokens e URL de destino não aparecem em relatório, JSON ou log.
- Desempenho e volume: a base atual tem 208 chunks em 7 documentos, então
  `list_ids` sobre o escopo é trivial. Paginação para bases grandes é
  preocupação de escala futura, não requisito desta fatia.
- Auditoria e observabilidade: cada execução de sincronização registra modo,
  escopo lógico e contagens de pontos previstos, inseridos, mantidos e
  removidos, sem credenciais, tokens ou URLs de destino. Esse registro é o
  insumo verificável da conferência de manifesto prevista na ideia original.

## Dependências

- BACKLOG-0001: precondição de segurança e origem das contagens auditáveis.
  Este item as consome para validar a operação; não as redefine.
- SPEC-0003: fornece `list_ids`, `query` e os contratos neutros usados pela
  validação; sem ela a conferência dependeria de SDK direto.

## Situações de erro

- Credencial, `config.yaml`, manifesto ou gabarito ausente: encerra com `2`
  antes de qualquer acesso remoto.
- Destino inacessível, escopo inexistente ou dimensão divergente da declarada
  em `embedding.dimensions`: encerra com `2` sem executar consultas.
- Divergência de identidade entre manifesto e destino, ou consulta fora do
  gabarito: encerra com `1`, com o detalhe no relatório e no JSON.
- Gabarito malformado: tratado como impedimento de validação, código `2`.

## Escopo

- Dentro: preflight somente leitura; conferência entre manifesto e destino
  remoto; roteiro verificável de consultas amplas, específicas e sem resposta;
  conferência de que as contagens da execução são observáveis e coincidem com
  o manifesto; remoção dos dois protótipos de diagnóstico.
- Fora: APM, tracing distribuído e métricas em serviço externo, que pertencem
  ao projeto-mãe `rag-pipeline`; qualquer mutação destrutiva no destino remoto;
  LLM de geração, que pertence ao BACKLOG-0010; paridade destrutiva de ChromaDB
  e Pinecone, que pertence ao BACKLOG-0009.

## Dúvidas, decisões e riscos

- Decisão confirmada em 2026-08-31, durante `$specsfy-setup`: o critério de
  "pronto" do M01 inclui logs estruturados de execução com escopo lógico e
  contagens. Registrada em `.specsfy/RULES.md`, seção Operação.
- Decisões D1 a D8 confirmadas pelo usuário em 2026-09-01, durante o
  refinamento deste item; cada uma está registrada em `Regras de negócio`.
- Resolvido: o formato do registro, antes aberto entre texto legível, JSON por
  linha ou ambos, foi decidido por D4 como relatório legível mais JSON de
  resultado.
- Risco: `SearchResult.score` é nativo de cada provider, então o
  `validacao.limiar_minimo` de D8 vale para o provider configurado naquela base
  e não é comparável entre Qdrant, ChromaDB e Pinecone. Aceitável porque cada
  `config.yaml` fixa um provider.
- Aberto, sem bloquear a especificação: o valor concreto do limiar para a base
  Vivo depende de calibragem empírica durante a execução.
- Aberto, sem bloquear a especificação: paginação de `list_ids` para bases
  grandes, irrelevante no volume atual.
- Inferência a confirmar na spec: o comando vive em `validate.py` na raiz,
  seguindo a convenção de `pipeline.py`, `search.py` e `chat.py`.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido em 2026-09-01 para `specs/draft/0004-validar-recuperacao-operacao/spec.md`. A fonte normativa passa a ser a spec; este item preserva apenas a proveniência.
