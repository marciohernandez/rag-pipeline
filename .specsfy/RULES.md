# Regras do sistema

Estas regras complementam as instruções dos agentes sem substituir specs ou
critérios de aceite. Stack confirmada em `.specsfy/STACK.md`: **Python 3.12+
com uv, LangChain, Pytest e bancos vetoriais Qdrant, ChromaDB e Pinecone**.

As regras abaixo foram confirmadas pela pessoa responsável. Registre novas
regras por `$specsfy-aux-rules`; não remova nem reescreva uma regra existente
sem confirmação explícita.

## Arquitetura

- Estruturar a lógica de negócio com orientação a objetos, encapsulamento, módulos focados, alta coesão e baixo acoplamento; scripts procedurais ficam limitados a ferramentas pontuais.

- Usar Factory ou Adapter para criação de providers, Strategy para comportamentos que variam por contexto e Repository para isolar regras de negócio do acesso à persistência.

- Manter imports de SDK de banco vetorial (`qdrant_client`, `chromadb`, `pinecone`, `langchain-qdrant`, `langchain-chroma`, `langchain-pinecone`) e de classes de embeddings (`OpenAIEmbeddings`, `HuggingFaceEmbeddings`, `langchain-huggingface`) confinados a `src/providers/`; o restante do repositório depende somente dos contratos neutros. `ChatOpenAI` em `chat.py` é a única exceção temporária, rastreada pelo BACKLOG-0010. Verificada por teste estático de AST em `tests/test_provider_boundaries.py`.

- Implementar toda nova orquestração de IA com LangGraph v1+ e componentes LangChain v1+; qualquer alternativa exige justificativa escrita antes da implementação.

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

- Manter .specsfy/DATABASE.md curado manualmente enquanto este componente não tiver schema relacional próprio: o scanner automático de $specsfy-aux-database varre .venv e confunde migrações internas de dependências Python (ex.: ChromaDB) com o schema do projeto, sobrescrevendo o conteúdo correto. Não executar esse scanner neste repositório até que ele passe a excluir diretórios de ambiente virtual Python (.venv, __pycache__, .pytest_cache). Revisar esta regra se este componente passar a persistir usuários, tenants ou ownership por conta própria — hoje essa responsabilidade pertence ao projeto-mãe rag-pipeline; tenant_id aqui é somente uma chave de escopo lógico de sincronização (SPEC-0002), sem tabela própria neste repositório.

## Processo e tracking

- Tratar o spec.md canônico como fonte da verdade de cada entrega e usar o Linear somente como projeção de acompanhamento da equipe; ao concluir cada fase do Specsfy, atualizar a issue vinculada com o estado, um resumo e o caminho da spec, sem registrar no Linear decisão divergente da fonte normativa.
