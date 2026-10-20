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

- Obter respostas de modelo de linguagem em `src/app` somente pelo contrato neutro `ChatModelAdapter`/`ChatMessage` de `src/pipeline/providers/contracts.py`, resolvido por `ProviderFactory.create_chat_model` e exposto pela fachada `src.pipeline.service` (`assistant_reply`); o SDK `ChatOpenAI` do adapter OpenRouter fica confinado a `src/pipeline/providers/llm/`, e `chat.py` segue como a única exceção temporária, rastreada pelo BACKLOG-0010 (SPEC-0021, DEC-002). Verificada por `tests/test_provider_boundaries.py`.

- Manter o assistente sem ferramentas de escrita: o modelo é chamado sem `bind_tools` e nenhum turno cria, altera ou apaga Workspace, Base, Execução, Consulta, Pessoa ou configuração; somente `conversas_assistente` e `mensagens_assistente` recebem escrita. Ampliar isso (ações confirmadas pela pessoa) exige spec própria (SPEC-0021, DEC-003).

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

- Tratar a chave de cada conexão de ingestão (SPEC-0026) como somente escrita: cifrá-la com Fernet usando a chave única injetada pelo entrypoint (`APP_CONEXOES_CHAVE` ou, em produção, `APP_CONEXOES_CHAVE_FILE` apontando para o secret `conexoes_chave` do Swarm), nunca devolvê-la nem registrá-la em API, log, manifesto, prévia ou mensagem de erro e exibir somente a máscara fixa. Não há rotação automática: trocar a chave de cifra exige recadastrar as chaves das conexões (DEC-003 e DEC-012 da SPEC-0026).

- Nunca colocar segredo nos argumentos de um job da fila: `process_base_task` recebe somente identificadores de conexão, lê e decifra a chave em memória no worker e revalida as URLs antes de conectar, porque os argumentos de job ficam persistidos no PostgreSQL (DEC-009 da SPEC-0026).

- Aceitar em conexões somente URLs `http` ou `https` sem usuário nem senha e recusar `localhost`, loopback, link-local, endereço não especificado e hosts de metadados da nuvem, a não ser que `APP_CONEXOES_PERMITIR_HOSTS_LOCAIS` esteja ligada explicitamente em desenvolvimento; redes internas do Swarm continuam permitidas (SPEC-0026, FR-001).

- Criar, conferir e trocar os secrets de produção do Swarm somente por `deploy/secrets.sh` (SPEC-0027): o valor entra pela entrada padrão do `docker secret create` e nunca em argumento, histórico do shell, arquivo, log, saída de erro ou stack file; cada secret é versionado (`<nome>_v<N>` em produção e `<nome>_local_v<N>` no ensaio local) e nunca é sobrescrito; o stack recebe a versão vigente pelas variáveis `*_SECRET`, resolvidas por `deploy/build_and_deploy.sh`, que verifica a existência de todos os secrets antes de qualquer build (DEC-001, DEC-002 e DEC-007 da SPEC-0027).

- Manter a troca de `postgres_password` e de `conexoes_chave` bloqueada por padrão: ela exige `--confirmar-consequencia`, a digitação do nome do secret e a leitura da consequência (Postgres: alterar a senha dentro do banco antes do deploy; conexões: recadastrar todas as chaves). O script apenas exibe o procedimento e nunca altera o banco (DEC-004 da SPEC-0027).

- Nunca incluir credenciais de conexão (chaves, senhas, tokens e URLs com credencial) no contexto enviado ao modelo do assistente, na resposta nem nos logs, nem para admin: `src/app/assistente_contexto.py` só devolve campos allowlisted e o copilot apenas informa se a conexão está configurada (SPEC-0031, DEC-006).

- Limitar toda consulta do copilot ao tenant, projeto e papel da identidade (o "Workspace da pessoa" da SPEC-0031 é o escopo de tenant e projeto), sem aceitar escopo vindo do modelo ou do texto da pergunta; a conexão e a divisão das coleções são restritas a owner e admin e o restante do estado operacional segue as permissões do papel (SPEC-0031, DEC-003, DEC-011, DEC-013).

## Operação

- Registrar em cada execução de sincronização o modo, o escopo lógico e as contagens de pontos previstos, inseridos, mantidos e removidos; nunca incluir credenciais, tokens ou URLs de destino nesse registro.

## Regras específicas do projeto

- Manter .specsfy/DATABASE.md curado manualmente: o scanner automático de $specsfy-aux-database só reconhece migrações Laravel/SQL/Prisma e `.env.example` com `DB_CONNECTION`; neste componente Python ele não encontra nada e sobrescreve o conteúdo correto com "A confirmar". Não executar esse scanner neste repositório até que ele passe a reconhecer os modelos SQLAlchemy de `src/app/models.py`. Editar `.specsfy/DATABASE.md` manualmente a cada mudança de schema.
- Atualizado pela SPEC-0012 (2026-09-04): este componente passou a persistir tenant/ownership por conta própria. Em `src/pipeline/`, `tenant_id` continua sendo somente uma chave de escopo lógico de sincronização (SPEC-0002), sem tabela própria. Em `src/app/` (backend de aplicação), `tenant_id` e `project_id` são colunas reais das tabelas `bases`, `executions` e `queries`, com papéis (owner/admin/member) aplicados por um token estático de demonstração (`src/app/auth.py`) — não uma autenticação completa de usuários. Cadastro, convite e login real continuam fora de escopo deste componente.

- Evitar as palavras `todo` e `Todo` no corpo de `specs/<estado>/<id>-<slug>/spec.md`, preferindo `cada`, `qualquer`, `inteiro` ou `na íntegra`. O validador `validate_spec.mjs` do Specsfy aplica `/\b(?:TODO|TBD|FIXME)\b|\[NEEDS CLARIFICATION/im` e o flag `i` faz a palavra portuguesa reprovar a spec com a mensagem genérica `Marcadores não resolvidos.`, que aponta para a causa errada; `toda`, `todos` e `todas` não disparam porque o `\b` não fecha depois do `o`. A mesma armadilha aparece **dentro** de outra palavra: `método`/`método de X` contém a substring `todo` cercada por caracteres não-alfanuméricos (espaço, pontuação), então também reprova — usar `função`, `mecanismo` ou `forma` em vez de `método` no corpo da spec. A trava local é `tests/test_spec_markers.py`, que antecipa a reprovação indicando arquivo, linha e trecho, e distingue a palavra portuguesa de um marcador real em caixa alta. Não reescrever `specs/inbox/` por causa desta regra: a captura preserva a formulação original da pessoa e não é lida pelo validador. Revisar esta regra e remover o teste quando o upstream `promovaweb/specsfy` corrigir o regex, retirando o flag `i`.
- Não usar a tag `[MIGRATION]` nas tarefas da seção 14. A versão atual do `validate_tasks.mjs` (`$specsfy-05-tasks`) só aceita as tags `P`, `TEST`, `TDD`, `CODE`, `DOC`, `OPS` e `US-NNN`; qualquer tarefa com `[MIGRATION]` é reprovada com `possui tags inválidas: MIGRATION` e o resultado fica `NOT READY` (substituiu o erro antigo de `MIGRATION_PATH` que não reconhecia `alembic/versions/`). Uma alteração de schema neste projeto (`alembic.ini`, `alembic/versions/*.py`) é uma tarefa `[CODE]` comum apontando para `alembic/versions/<revisão>_<slug>.py` (mais o model em `src/app/models.py` quando aplicável, já que a suíte de app materializa o schema por `metadata.create_all`, que não altera tabela existente). A disciplina de migration é preservada por: (a) o caminho versionado na linha da tarefa; (b) o item `VERIFY` registrando dois comandos aprovados pelo `check_database_safety.mjs` — `uv run alembic upgrade head` no banco de teste (`rag_pipeline_test`) e `uv run alembic current`; (c) o comentário `specsfy:evidence` (Evidence Contract 1) com a revisão em `files`. Revisar esta regra se o upstream `promovaweb/specsfy` reintroduzir a tag `[MIGRATION]` com suporte a `alembic/versions/`.

- Atualizado pela SPEC-0020 (2026-09-21): autenticar o backend e o frontend exclusivamente por Pessoa e Sessão persistidas; resolver tenant, projeto e papel pelo vínculo da pessoa no banco a cada requisição; recusar tokens estáticos; nunca inferir papel pelo texto do token; preservar ao menos um owner ativo por tenant e projeto; e nunca apagar Pessoas, apenas desativá-las, para preservar autoria.

- Tratar como superada pela SPEC-0020 a nota da SPEC-0012 que limitava este componente a tokens estáticos e deixava login real fora de escopo: src/app autentica exclusivamente por Pessoa e Sessão persistidas, e o frontend entra por e-mail e senha.

- Impedir que admin crie, promova, rebaixe, edite, desative, reative ou redefina a senha de owner; somente owner pode agir sobre outro owner. Nunca apagar Pessoa: desativar preserva a identidade e a autoria histórica.

## Processo e tracking

- Tratar o spec.md canônico como fonte da verdade de cada entrega e usar o Linear somente como projeção de acompanhamento da equipe; ao concluir cada fase do Specsfy, atualizar a issue vinculada com o estado, um resumo e o caminho da spec, sem registrar no Linear decisão divergente da fonte normativa.

- Abrir uma branch por unidade de integração, com o nome declarando exatamente o que ela carrega: `spec/<NNNN>-<slug>` para o trabalho de uma única spec (o slug é o da pasta da spec, sem traduzir), `chore/<slug>` para tooling, CI e documentação sem spec, e `fix/<slug>` para correção fora de spec. Uma branch nunca carrega duas specs. Esta é a formulação precisa da regra anterior de "branch própria para cada fase de desenvolvimento", que era ambígua: sob ela, `feat/0013-cobrir-backends-reais-vector-store` acumulou 40 commits em 4 dias cobrindo as SPEC-0005, 0010, 0011, 0012 e 0013 mais o fechamento do M01 — e o CI ficou vermelho por 3 dias sem ninguém notar, porque nada chegava à `main` para dar o alarme (auditoria de 2026-09-07).

- Integrar toda branch à `main` por pull request com os dois jobs do CI verdes; a branch de uma spec só abre PR depois que a spec alcança `Complete` (Delivery Gate `Passed`), e é apagada após o merge. Não trabalhar direto na `main`.

- Não criar branch de milestone. O marco é uma projeção sobre specs — vive no cabeçalho `| Milestones |` de cada spec, em `specs/milestones/<ID>.md` e no bloco derivado por `specsfy milestones sync` — e fecha por estado das specs, não por merge. Ao fechar um marco, registrar uma tag anotada com o ID do marco (`M01`, `M02`...) no commit de fechamento em `main`, contendo escopo, contagem de specs e as condições de saída verificadas. Uma branch `release/<ID>` só nasce a partir da tag e sob demanda, se houver versão implantada que não possa receber o que já entrou na `main`; nunca preventivamente.

## Produção: serviços de dados externos

- Atualizado pela SPEC-0041 (2026-10-19): em produção o Postgres e o Qdrant são externos ao Swarm e o stack os alcança só por variáveis e secrets, sem host, usuário, senha, chave ou domínio reais no repositório; o Postgres exige TLS (`sslmode=require` no mínimo); o prefixo `APP_COLECAO_PREFIXO` protege as coleções já existentes no Qdrant compartilhado e vale apenas para coleções criadas depois de configurado.
