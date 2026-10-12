# Inbox: apagar_base ignora a coleção da Base e falha com 404 no Qdrant

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-05T16:51:54Z |
| Slug | apagar-base-ignora-a-colecao-da-base-e-falha-com-404-no-qdrant |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `b15e3bcd7766702227b3757568bafc3e8db1a820ae88fca0f70e352b6161c026` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Ao tentar apagar uma Base pela interface (botão Apagar base na tela da Base), a exclusão falha com a mensagem Não foi possível apagar a base. Tente novamente. Observado em 2026-10-05 no ensaio local do stack Swarm (SPEC-0022). O backend registra UnreliableScopeReadError: A releitura paginada do escopo no Qdrant falhou; sincronização bloqueada, causada por um 404 do Qdrant: coleção rag-pipeline-app não existe. A Base havia sido criada com a coleção vivo test (escolhida no upload) e os 23 chunks estão em vivo test. Indexação e consulta usam base.collection_name (src/app/routers/executions.py e queries.py), mas apagar_base (src/app/routers/bases.py, delete_scope) monta a configuração com a coleção padrão do sistema (APP_VECTOR_STORE_COLLECTION, rag-pipeline-app) e ignora a coleção da Base. Efeito: apagar qualquer Base com coleção própria falha; se a coleção padrão existisse, a exclusão deixaria vetores órfãos na coleção real. Nada foi apagado na falha. Reprodução: criar Base com coleção própria, indexar e clicar em Apagar base.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A exclusão de uma Base usa a coleção padrão do sistema em vez da coleção da própria Base, e por isso falha quando a coleção própria é diferente.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Não é possível apagar Bases criadas com coleção própria (ex.: vivo test); o endpoint DELETE /bases/{id} devolve erro porque consulta rag-pipeline-app, que não existe no Qdrant.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Owner/admin e demais pessoas com papel de escrita que apagam Bases.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Apagar uma Base remove seus vetores da coleção correta e a Base some da listagem, sem deixar resíduos.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Divergência entre apagar_base (coleção padrão de settings.vector_store) e executions/queries/assistente (base.collection_name). Relacionado à compensação de SPEC-0018 e ao controle de coleção de SPEC-0019.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Se a coleção padrão existir, a exclusão pode deixar vetores órfãos na coleção real da Base; a idempotência do DELETE depende de ler a coleção certa.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possível fix pequeno em branch fix/ com teste de regressão que reproduza a falha; avaliar se a mesma divergência afeta outros caminhos que usam settings.vector_store.

## Pontos a revisar no futuro

**A revisar:** Confirmar se o mesmo problema ocorre com outros providers; decidir se Bases vazias por upload que falhou deveriam ser limpas automaticamente; coleção vivo test contém espaço no nome, verificar se isso interfere.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
