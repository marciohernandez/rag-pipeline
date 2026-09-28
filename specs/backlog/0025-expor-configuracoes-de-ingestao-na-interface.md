# Backlog: Expor configurações de ingestão na interface

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0025 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-17 |
| Spec promovida | Nenhuma |

## Ideia original

todas as variáveis configuráveis devem estar aki e tambem ter uma forma mais organizada

## Problema percebido

Parâmetros do pipeline de ingestão já existem em código (estratégia de chunking MarkdownHeaderTextSplitter/RecursiveCharacterTextSplitter, chunk_size, chunk_overlap em src/pipeline/chunker.py; nome de coleção do vector store em src/pipeline/indexing.py, hoje com default global 'rag_docs') mas só são ajustáveis via config.yaml/CLI, não pela interface.

## Pessoa afetada ou beneficiada

Marcio e quem opera o pipeline pela interface, sem precisar editar arquivos de configuração ou reimplantar.

## Resultado ou valor esperado

Tela de configurações no frontend onde é possível escolher a estratégia de chunking (splitter), o tamanho de chunk, se há overlap, e o nome da coleção do banco vetorial usada.

## Contexto

Escopo inicial: estratégia/tamanho/overlap de chunk e nome de coleção, confirmados nesta conversa. Provider de LLM plugável já é backlog próprio (0010); escolha de backend de vector store (Qdrant/Chroma/Pinecone) fica registrada aqui como sinal, a aprofundar. Relação com o item "Projetos" (próximo item a registrar nesta conversa): a escolha de coleção por conjunto de arquivos depende de como "Projetos" vier a existir.

## Referências relacionadas

- `specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md` (origem: captura original, mesma conversa que originou este item).
- `specs/backlog/0010-provider-llm-plugavel.md` (backlog relacionado: configuração de provider de LLM já tratada separadamente).
- `src/pipeline/chunker.py` e `src/pipeline/indexing.py` (comportamento atual já configurável em código, ainda não exposto na UI).

## Comportamento esperado

- **Decisão:** os parâmetros (splitter, tamanho de chunk, overlap, nome de coleção) não formam uma tela de "Configurações" global e separada — são escolhidos por upload/Base, no momento de enviar os arquivos, dentro de um Workspace (item 0026). Isso permite que Bases diferentes do mesmo Workspace usem estratégias diferentes (ex.: uma coleção "produtos" com um splitter, outra "políticas" com outro).
- **Decisão:** o campo de estratégia de chunking oferece as opções já suportadas pelo pipeline hoje — `MarkdownHeaderTextSplitter` e `RecursiveCharacterTextSplitter` (`src/pipeline/chunker.py`).
- A esclarecer: valores padrão pré-preenchidos no formulário de upload (para quem não quiser configurar nada) e seus limites mínimo/máximo aceitáveis para tamanho de chunk e overlap.

## Regras de negócio

- **Decisão (autorização):** somente `owner` e `admin` podem definir esses parâmetros, por fazerem parte do formulário de upload — `member` não envia arquivos (mesma regra do item 0026 e de Bases hoje, `require_write_role`).

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado; depende do detalhamento do formulário de upload (Contrato de experiência de interface), compartilhado com o item 0026.

## Qualidades e operação

- Segurança: sem exposição nova — mesmos parâmetros já existentes no backend, agora visíveis a quem já tem permissão de upload.
- Privacidade: não aplicável — parâmetros técnicos de processamento, sem dado pessoal.
- Desempenho e volume: a esclarecer — se chunk_size/overlap muito grandes devem ter validação de limite na interface.
- Auditoria e observabilidade: a avaliar; recomenda-se registrar os parâmetros usados em cada execução, já que `manifesto de execução` (`.specsfy/DATABASE.md`) já guarda `collection_name`.

## Dependências

- Item 0026 (Workspace) — o formulário de upload onde esses parâmetros aparecem é o mesmo formulário de criar uma Base dentro de um Workspace.

## Situações de erro

- A esclarecer: o que a interface mostra se a pessoa informar um tamanho de chunk ou overlap fora de um limite aceitável.

## Escopo

- Dentro: campo de escolha de splitter, tamanho de chunk, overlap e nome de coleção no formulário de upload de uma Base.
- Fora: escolha de backend de vector store (Qdrant/Chroma/Pinecone) — apenas sinalizado aqui, não aprofundado; provider de LLM plugável (já é o item 0010).

## Dúvidas, decisões e riscos

- **Resolvida:** escopo por upload/Base, não uma tela de configurações global (ver Comportamento esperado).
- **Aberto:** valores padrão e limites mínimo/máximo para tamanho de chunk e overlap.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente (falta Gherkin/critérios de aceite, a produzir na especificação).
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco (limites de chunk/overlap ainda a esclarecer).
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
