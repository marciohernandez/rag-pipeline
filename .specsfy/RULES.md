# Regras do sistema

Estas regras complementam as instruções dos agentes sem substituir specs ou
critérios de aceite. Stack confirmada em `.specsfy/STACK.md`: **Python 3.12+
com uv, LangChain, Pytest e Qdrant como único provider concreto de vector
store** (ChromaDB e Pinecone removidos pela SPEC-0010).

As regras abaixo foram confirmadas pela pessoa responsável. Registre novas
regras por `$specsfy-aux-rules`; não remova nem reescreva uma regra existente
sem confirmação explícita.

## Arquitetura

- Estruturar a lógica de negócio com orientação a objetos, encapsulamento, módulos focados, alta coesão e baixo acoplamento; scripts procedurais ficam limitados a ferramentas pontuais.

- Usar Factory ou Adapter para criação de providers, Strategy para comportamentos que variam por contexto e Repository para isolar regras de negócio do acesso à persistência.

- Manter imports de SDK de banco vetorial (`qdrant_client`; `langchain-qdrant` foi avaliado e removido por falta de uso, ver DEC-011) e de classes de embeddings (`OpenAIEmbeddings`, `HuggingFaceEmbeddings`, `langchain-huggingface`) confinados a `src/pipeline/providers/`; o restante do repositório depende somente dos contratos neutros. `ChatOpenAI` em `chat.py` é a única exceção temporária, rastreada pelo BACKLOG-0010. Verificada por teste estático de AST em `tests/test_provider_boundaries.py`. `chromadb`, `pinecone`, `langchain-chroma` e `langchain-pinecone` foram removidos do projeto pela SPEC-0010 e não se aplicam mais a esta regra.

- Implementar toda nova orquestração de IA com LangGraph v1+ e componentes LangChain v1+; qualquer alternativa exige justificativa escrita antes da implementação.

- Manter src/app/ dependente somente da fachada src.pipeline.service; proibir imports de outros módulos de src.pipeline a partir de src/app e qualquer import de src.app a partir de src.pipeline, com verificação estática em tests/test_application_boundaries.py.

- Manter os módulos sob `src/pipeline/` livres de `python-dotenv`: eles não carregam o `.env` nem chamam `load_dotenv`, apenas leem variáveis já presentes no ambiente. A carga do `.env` é responsabilidade de cada entrypoint `.py` da raiz, que chama `load_env()` de `src/bootstrap.py` no início de `main()`. Verificada por duas varreduras estáticas em `tests/test_env_bootstrap.py` (SPEC-0009).

- Manter Qdrant como único provider concreto de vector store; a abstração multi-provider (contrato neutro em src/pipeline/providers/contracts.py, backend port, ProviderFactory extensível e InMemoryVectorStoreAdapter como oráculo) permanece aberta. Adicionar um provider é: novo módulo em src/pipeline/providers/vectorstores/, entrada em ProviderFactory._VECTOR_STORES e parametrização da suíte de conformidade — sem alterar contracts.py nem a superfície pública da factory. ChromaDB e Pinecone foram removidos pela SPEC-0010 por não estarem escolhidos para uso.

## Código e qualidade

- Criar e usar uma branch própria para cada fase de desenvolvimento; não trabalhar diretamente na branch principal.

- Executar Ruff e a suíte Pytest antes de integrar este componente ao projeto-mãe.

- Usar Specsfy como workflow normativo único deste repositório; manter backlog, especificação, gates e tarefas nos caminhos canônicos do framework e não criar plan.md, tasks.md ou artefatos paralelos do GitHub SpecKit.

- Manter `chat.py`, `demo_rag.py` e `search.py` livres de identidade, produto ou domínio de cliente escritos no código; derivar a identidade operacional de `projeto.nome` e `projeto.descricao` e verificar a neutralidade pelas guardas estática e positiva de `tests/test_client_neutrality.py`.

## Testes

- Executar Pytest antes de integrar mudanças; componentes críticos devem seguir Red-Green-Refactor, com testes escritos antes da implementação.

- Manter um workflow de integração contínua que execute Ruff e a suíte Pytest a cada push de branch de fase; a conclusão do milestone M0 exige esse workflow verde, sem depender de execução manual.

## Segurança e privacidade

- Nunca versionar ou expor credenciais, senhas, tokens ou configuração sensível; manter segredos fora do repositório e centralizar o acesso à configuração.

## Operação

- Registrar em cada execução de sincronização o modo, o escopo lógico e as contagens de pontos previstos, inseridos, mantidos e removidos; nunca incluir credenciais, tokens ou URLs de destino nesse registro.

## Regras específicas do projeto

- Manter .specsfy/DATABASE.md curado manualmente: o scanner automático de $specsfy-aux-database só reconhece migrações Laravel/SQL/Prisma e `.env.example` com `DB_CONNECTION`; neste componente Python ele não encontra nada e sobrescreve o conteúdo correto com "A confirmar". Não executar esse scanner neste repositório até que ele passe a reconhecer os modelos SQLAlchemy de `src/app/models.py`. Editar `.specsfy/DATABASE.md` manualmente a cada mudança de schema.
- Atualizado pela SPEC-0012 (2026-09-04): este componente passou a persistir tenant/ownership por conta própria. Em `src/pipeline/`, `tenant_id` continua sendo somente uma chave de escopo lógico de sincronização (SPEC-0002), sem tabela própria. Em `src/app/` (backend de aplicação), `tenant_id` e `project_id` são colunas reais das tabelas `bases`, `executions` e `queries`, com papéis (owner/admin/member) aplicados por um token estático de demonstração (`src/app/auth.py`) — não uma autenticação completa de usuários. Cadastro, convite e login real continuam fora de escopo deste componente.

- Evitar as palavras `todo` e `Todo` no corpo de `specs/<estado>/<id>-<slug>/spec.md`, preferindo `cada`, `qualquer`, `inteiro` ou `na íntegra`. O validador `validate_spec.mjs` do Specsfy aplica `/\b(?:TODO|TBD|FIXME)\b|\[NEEDS CLARIFICATION/im` e o flag `i` faz a palavra portuguesa reprovar a spec com a mensagem genérica `Marcadores não resolvidos.`, que aponta para a causa errada; `toda`, `todos` e `todas` não disparam porque o `\b` não fecha depois do `o`. A mesma armadilha aparece **dentro** de outra palavra: `método`/`método de X` contém a substring `todo` cercada por caracteres não-alfanuméricos (espaço, pontuação), então também reprova — usar `função`, `mecanismo` ou `forma` em vez de `método` no corpo da spec. A trava local é `tests/test_spec_markers.py`, que antecipa a reprovação indicando arquivo, linha e trecho, e distingue a palavra portuguesa de um marcador real em caixa alta. Não reescrever `specs/inbox/` por causa desta regra: a captura preserva a formulação original da pessoa e não é lida pelo validador. Revisar esta regra e remover o teste quando o upstream `promovaweb/specsfy` corrigir o regex, retirando o flag `i`.
- Não usar a tag `[MIGRATION]` nas tarefas da seção 14. A versão atual do `validate_tasks.mjs` (`$specsfy-05-tasks`) só aceita as tags `P`, `TEST`, `TDD`, `CODE`, `DOC`, `OPS` e `US-NNN`; qualquer tarefa com `[MIGRATION]` é reprovada com `possui tags inválidas: MIGRATION` e o resultado fica `NOT READY` (substituiu o erro antigo de `MIGRATION_PATH` que não reconhecia `alembic/versions/`). Uma alteração de schema neste projeto (`alembic.ini`, `alembic/versions/*.py`) é uma tarefa `[CODE]` comum apontando para `alembic/versions/<revisão>_<slug>.py` (mais o model em `src/app/models.py` quando aplicável, já que a suíte de app materializa o schema por `metadata.create_all`, que não altera tabela existente). A disciplina de migration é preservada por: (a) o caminho versionado na linha da tarefa; (b) o item `VERIFY` registrando dois comandos aprovados pelo `check_database_safety.mjs` — `uv run alembic upgrade head` no banco de teste (`rag_pipeline_test`) e `uv run alembic current`; (c) o comentário `specsfy:evidence` (Evidence Contract 1) com a revisão em `files`. Revisar esta regra se o upstream `promovaweb/specsfy` reintroduzir a tag `[MIGRATION]` com suporte a `alembic/versions/`.

## Processo e tracking

- Tratar o spec.md canônico como fonte da verdade de cada entrega e usar o Linear somente como projeção de acompanhamento da equipe; ao concluir cada fase do Specsfy, atualizar a issue vinculada com o estado, um resumo e o caminho da spec, sem registrar no Linear decisão divergente da fonte normativa.
