# Backlog: Fluxo completo de ingestão inspirado nos Document Stores do Flowise

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0025 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | A esclarecer |
| Funcionalidade | Preparação e indexação de documentos |
| Tipo | Melhoria |
| Prioridade | Terceira na ordem confirmada: corrigir exclusão, indicadores de processamento, fluxo de ingestão |
| Milestones | |
| Criado em | 2026-09-17 |
| Spec promovida | specs/planned/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md (SPEC-0026, Planned) |

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

## Ampliação confirmada em 2026-10-05

### Origem e decisão

Resposta literal do usuário: “1”. Normalização: **ampliar este backlog
existente com o fluxo completo de ingestão baseado no Flowise**, em vez de
criar outro item ou limitar a primeira entrega aos parâmetros de upload.
Preservar ID BACKLOG-0025, caminho e formulação original. Nenhuma spec
derivada existe; Status continua Refining.

A captura integral do pedido e as referências das dez imagens permanecem em
`specs/inbox/2026-10-05-170632-fluxo-de-ingestao-inspirado-nos-document-stores-do-flowise.md`.
As imagens foram descritas nessa captura, mas não estão disponíveis para
nova inspeção nesta rodada. A análise externa desta rodada usa documentação
e código oficiais, sem afirmar que revisou os anexos.

### Problema e resultado atualizados

A interface atual cria a Base e agenda a execução completa logo após o
upload. Marcio e a equipe querem controlar carregamento, divisão, prévia e
publicação dos documentos pela interface, seguindo inicialmente a jornada
dos Document Stores do Flowise. O resultado esperado é preparar e revisar
os chunks antes de gerar embeddings e publicar no Qdrant.

### Pedido já declarado e incorporado

- Workspace com nome e descrição.
- Seleção de Document Loader; na fase atual, receber os `.md` produzidos pela
  fase 1 com Text File Loader. A escolha de loaders para outros formatos
  pertence à fase 1 conforme o pedido; não implica implementar todos agora.
- Upload, Additional Metadata e Omit Metadata Keys.
- Seleção de splitter e seus parâmetros, com prévia dos chunks. Markdown
  comum e Q&A podem exigir tratamento diferente; organização final dos
  grupos e precedência das configurações continuam em descoberta.
- Upsert com etapas Embeddings, Vector Store e Record Manager, tomando
  OpenAI Custom Embedding e Qdrant como referências dos prints descritos.
- As ações Preview & Process, View & Edit Chunks, Upsert Chunks, View API e
  Delete aparecem na referência. Seu comportamento no produto ainda exige
  detalhamento; não são contratos prontos para implementação.

### Decisões anteriores preservadas

- Configuração por upload/Base dentro do Workspace; sem tela global de
  parâmetros de ingestão. Bases diferentes podem usar estratégias diferentes.
- Owner/admin podem enviar e configurar; member não envia arquivos.
- O projeto já separa configuração não sensível de credenciais; isso é uma
  restrição atual, não uma decisão sobre uma nova tela de conexões.
- O suporte local a Q&A preserva um par por chunk e ativa por `splitter: qa`
  no frontmatter, com separador `++++` (SPEC-0002). Não inferir que Q&A e
  Markdown comum exigem Workspaces separados.

A lista anterior de escopo representa o refinamento de setembro. Sua
limitação a quatro campos foi ampliada pela decisão desta rodada. A escolha
de múltiplos bancos vetoriais permanece aberta: seguir o modelo visual do
Flowise não confirma implementar seu catálogo inteiro de providers.

### Análise das fontes em 2026-10-05

**Observação local:** `UploadBaseSheet.criar` chama `agendarEAbrir`; o worker
prepara e sincroniza na mesma execução. Coleção e metadados adicionais por
Base já existem (SPEC-0019), portanto não são capacidades ausentes.
`src/pipeline/loader.py` mantém frontmatter YAML; `chunker.py` aplica
configuração do documento antes da global e possui header, character e qa.
A precedência de uma nova configuração de formulário ainda deve ser definida.

**Observação externa:** a documentação oficial do Flowise separa loader,
splitter, prévia, processamento, edição dos chunks e configuração de upsert.
Record Manager é opcional na referência. O nó Text File usa TextLoader do
LangChain JavaScript e aceita `.md`; o nosso loader Python tem preservação
de frontmatter própria. Reutilizar o conceito não exige substituir o parser
local ou importar código JavaScript no backend.

**Proposta de jornada, a detalhar:** Workspace → envio/configuração → prévia
→ preparação dos chunks → revisão → configuração de upsert → indexação
→ acompanhamento/consulta. Separar a geração de chunks da publicação é uma
mudança de comportamento a especificar, não uma alteração aplicada agora.

### Referências relacionadas à ampliação

- `specs/inbox/2026-10-05-170632-fluxo-de-ingestao-inspirado-nos-document-stores-do-flowise.md`: origem integral.
- `specs/completed/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md`: spec relacionada; Base/Workspace, coleção e metadados já entregues.
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md`: spec relacionada; contrato Q&A já entregue.
- `specs/backlog/0010-provider-llm-plugavel.md`: backlog relacionado; provider de LLM não é sinônimo de provider de embeddings.
- `INTERFACE.md`, `DESIGNSYSTEM.MD`, `docs/flows.md`: documentação relacionada; Next App Router/React/Tailwind/shadcn Base UI, componentes existentes e jornada atual.
- `frontend/src/features/bases/UploadBaseSheet.tsx`, `src/app/tasks.py`, `src/pipeline/loader.py`, `src/pipeline/chunker.py`, `config.example.yaml`: evidência local.
- https://docs.flowiseai.com/using-flowise/document-stores : documentação oficial consultada em 2026-10-05.
- https://github.com/FlowiseAI/Flowise/blob/main/packages/components/nodes/documentloaders/Text/Text.ts : código oficial do Text File consultado em 2026-10-05, branch main (referência mutável).

### Lacunas materiais em descoberta

1. **Resolvida:** cadastrar conexões reutilizáveis de embeddings e Qdrant
   pela interface e selecioná-las na etapa de upsert. Reutilização por
   owner/admin da mesma equipe e projeto, em qualquer Workspace. Permissões
   de gestão confirmadas: owner e admin administram qualquer conexão. Campos,
   tratamento de segredos e auditoria ainda precisam de descoberta. O ciclo de
   vida foi confirmado: desativar preserva vínculos/histórico; novo upsert
   exige conexão ativa; exclusão definitiva somente sem uso.
2. Relação entre Workspace, Base e registros de loader, escopo da coleção e
   possibilidade de adicionar novos envios sem substituir o conteúdo anterior.
3. Precedência formulário/frontmatter, formatos mistos, parâmetros padrão e
   limites; separar comportamento Q&A de parâmetros que quebrariam seus pares.
4. Prévia versus chunks persistidos; edição/exclusão, nova preparação e
   efeito sobre chunks já publicados.
5. Providers efetivos de embeddings, Vector Store e Record Manager;
   configurações expostas, compatibilidade de dimensões e comportamento de
   falha/repetição.
6. Composição de telas, ações/menu, navegação e ciclo de vida dos dados.

### Diagnóstico atualizado

Captura mínima atendida e ampliação registrada. Ainda não pronto para
especificação: conexões, dados, composição e contratos precisam de decisões.
As marcações anteriores de prontidão permanecem como histórico do escopo
anterior; não aprovam a entrega ampliada. Nenhum código, teste, schema ou
gate foi alterado por este refinamento.

### Rodada atual

Área: Integrações. Pergunta 1: como oferecer conexões de embeddings e Qdrant
na etapa de upsert? Opções: 1. cadastro e seleção de conexões reutilizáveis na interface
(recomendado); 2. somente conexões preparadas no servidor; 3. ambas as formas.
Resposta literal: “1”. Normalização: cadastrar conexões reutilizáveis pela
interface e selecioná-las no upsert. Decisão confirmada em 2026-10-05.
Não confirma compartilhamento global, campos ou permissões novas.

### Descoberta de dados — próxima rodada

Área: Dados. Pergunta 1: quem poderá reutilizar uma conexão cadastrada?
1. Owner/admin da mesma equipe e projeto ativo, em seus Workspaces
(recomendado, compatível com o isolamento atual).
2. Somente a pessoa que cadastrou a conexão.
3. Owner/admin apenas no Workspace ao qual a conexão estiver vinculada.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: owner/admin da mesma equipe e projeto
podem reutilizar conexões em qualquer Workspace. Confirmado em 2026-10-05.
Isso confirma compartilhamento e uso; não confirma exibição de segredos nem
quem poderá editar/excluir as conexões.

### Descoberta de dados — ciclo de vida (rodada 2)

Área: Dados. Pergunta 1: o que deve acontecer ao retirar uma conexão já
usada por Bases?
1. Desativar, preservando vínculos e histórico; exigir conexão ativa para
novo upsert. Apagar definitivamente somente quando não houver uso
(recomendado).
2. Impedir desativação/exclusão enquanto houver Bases vinculadas.
3. Exigir troca da conexão em todas as Bases antes de permitir exclusão.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: desativar uma conexão em uso preserva
vínculos e histórico; o próximo upsert exige conexão ativa; excluir
definitivamente somente quando não houver uso. Confirmado em 2026-10-05.
Não alterar nem remover automaticamente os vetores já publicados.

### Descoberta de dados — administração (rodada 3)

Área: Dados. Pergunta 1: quem poderá cadastrar, editar, desativar e excluir
conexões dentro da equipe e projeto?
1. Owner e admin, seguindo a administração atual do produto (recomendado).
2. Somente owner; admin apenas seleciona conexões no upsert.
3. Owner administra todas; admin administra somente as que cadastrou.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: owner e admin cadastram, editam,
desativam e excluem qualquer conexão da equipe e projeto, sem distinção de
quem a cadastrou; `member` não administra nem seleciona conexões. Confirmado
em 2026-10-06. Não confirma exibição ou armazenamento de segredos, campos da
conexão, nem trilha de auditoria das alterações.

### Descoberta de dados — segredos das conexões (rodada 4)

Área: Dados. Pergunta 1: como tratar a chave (segredo) de uma conexão depois
de cadastrada?
1. Somente escrita: a interface nunca devolve a chave (aparece mascarada);
trocar exige informar uma nova; a chave fica cifrada no servidor
(recomendado).
2. Referência a segredo provisionado no servidor (ex.: Docker Swarm, item
0030); a interface nunca recebe a chave.
3. Owner pode revelar a chave; admin vê só mascarada.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: segredo somente escrita — a interface e
a API nunca devolvem a chave, só uma forma mascarada; trocar exige informar
nova chave; armazenamento cifrado no servidor. Confirmado em 2026-10-06.
Implicações a tratar na spec: onde fica a chave de cifra (relação com
`specs/backlog/0030-gestao-de-secrets-de-producao-via-docker-swarm.md`),
não registrar a chave em logs, manifesto de execução ou prévias. Não confirma
os campos não secretos da conexão nem a auditoria das alterações.

### Descoberta de integrações — tipos de conexão (rodada 5)

Área: Integrações. Pergunta 1: quais tipos de conexão a primeira entrega
oferece?
1. Enxuto: embeddings OpenAI (modelo e URL base opcionais para endpoints
compatíveis) e Qdrant; demais providers depois (recomendado).
2. Embeddings OpenAI e Qdrant, mais modelo local de embeddings.
3. Catálogo ampliado: OpenAI, outros providers de embeddings, Qdrant, Chroma
e Pinecone, seguindo o Flowise.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: a primeira entrega oferece somente dois
tipos de conexão — embeddings OpenAI (modelo e URL base opcionais para
endpoints compatíveis com a API) e Qdrant. Chroma, Pinecone e outros
providers de embeddings ficam fora desta entrega (ver
`specs/backlog/0009-paridade-mirror-chroma-pinecone.md`). Confirmado em
2026-10-06. Não confirma Record Manager nem compatibilidade de dimensões.

### Descoberta de integrações — dimensão dos vetores (rodada 6)

Área: Integrações. Pergunta 1: o que fazer quando a dimensão do modelo de
embeddings difere da coleção existente?
1. Bloquear antes de publicar, com mensagem clara; nenhum vetor gravado
(recomendado).
2. Avisar e permitir criar nova coleção com a dimensão correta.
3. Deixar o Qdrant recusar e mostrar o erro.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: antes do upsert, comparar a dimensão do
modelo de embeddings com a da coleção; se divergirem, bloquear a publicação
com mensagem clara e não gravar nenhum vetor. Confirmado em 2026-10-06.
Pendência para a spec: como obter a dimensão do modelo (consulta ao provider
ou valor declarado na conexão) e como tratar coleção ainda inexistente.

### Descoberta de integrações — Record Manager (rodada 7)

Área: Integrações. Pergunta 1: como tratar o Record Manager nesta entrega?
1. Reaproveitar a sincronização atual (SPEC-0002) como comportamento padrão,
sem etapa nem conexão própria; a interface mostra inseridos, mantidos e
removidos (recomendado).
2. Etapa opcional por upsert, ligável/desligável.
3. Fora desta entrega; sincronização atual sempre, Record Manager como
evolução futura.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: não haverá etapa nem conexão de Record
Manager; o upsert usa a sincronização por escopo lógico já existente
(SPEC-0002) e a interface exibe as contagens de pontos inseridos, mantidos e
removidos. Confirmado em 2026-10-06.

### Descoberta de dados — prévia e chunks (rodada 8)

Área: Dados. Pergunta 1: o que a prévia e a revisão dos chunks significam?
1. Prévia descartável, sem persistir; aprovar gera e publica; sem edição ou
exclusão de chunks individuais (recomendado).
2. Chunks persistidos e editáveis antes do upsert.
3. Prévia descartável agora; persistência e edição em spec futura.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: a prévia calcula os chunks sem
persisti-los; ao aprovar, a execução gera e publica. Não há edição nem
exclusão de chunks individuais; ajustar significa alterar parâmetros e rever
a prévia. Confirmado em 2026-10-06. Consequência: "View & Edit Chunks" do
Flowise fica fora deste escopo.

### Síntese do ciclo — 2026-10-06

Limite de oito perguntas do ciclo atingido (conexões: compartilhamento,
ciclo de vida, administração, segredos, tipos, dimensão, Record Manager e
prévia). Decidido: conexões reutilizáveis cadastradas pela interface,
administradas por owner/admin, segredo somente escrita cifrado, tipos
OpenAI embeddings e Qdrant, bloqueio por dimensão divergente, sem Record
Manager próprio (reuso da SPEC-0002), prévia descartável sem edição de chunks.

**Lacunas abertas (não perguntadas, por limite):**
- Relação Workspace/Base/loader, escopo da coleção e adicionar envios sem
  substituir o conteúdo anterior.
- Precedência formulário × frontmatter, formatos mistos, padrões e limites de
  chunk_size/overlap; proteção do comportamento Q&A.
- Origem da dimensão do modelo e coleção ainda inexistente.
- Auditoria das alterações em conexões; guarda da chave de cifra (item 0030).
- Área Interface: telas, menus, navegação, formulários, composição e estados
  (nenhuma pergunta feita ainda; área própria, com limite próprio de oito).

Status permanece Refining. Não pronto para `$specsfy-03-specify`.

## Descoberta de Interface — 2026-10-06

### Análise do sistema atual (preservar / mudar)

Stack observada em `INTERFACE.md`: Next.js 16 App Router, React 19,
TypeScript, Tailwind v4, shadcn/ui `base-nova` (Base UI), registry ReUI
configurado sem blocos instalados, Vitest + Testing Library. Não introduzir
outra biblioteca por suposição.

Preservar: navegação (Workspaces para todos, Pessoas para owner/admin,
`MenuPessoa`), trilha Equipe → Workspaces → Workspace → Base, `PageHeader`
único, `DataGrid` com coluna `ID` e linha clicável, `Sheet` para formulários
curtos, `Dialog` para confirmações, `Button loading` e
`IndicadorProcessamento` (SPEC-0025), `PainelProgresso` e
`FormularioConsulta` na Base.

Mudar: o envio hoje cria a Base e agenda a execução completa
(`UploadBaseSheet.criar` → `agendarEAbrir`); o novo fluxo separa configurar,
prévia e publicação. Surge uma superfície de conexões (somente owner/admin).

### Pergunta 1 (Interface) — onde vive o fluxo

1. Página própria com etapas, aberta pelo botão do Workspace
   (ex.: `/workspaces/[id]/bases/nova`): Arquivos → Divisão → Prévia →
   Publicação (recomendado).
2. Manter e ampliar o `UploadBaseSheet` com as etapas.
3. Híbrido: `UploadBaseSheet` para enviar/configurar; prévia e publicação
   como etapas da página da Base.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: o fluxo de envio, configuração, prévia
e publicação é uma página própria com etapas (Arquivos → Divisão → Prévia →
Publicação), aberta a partir do Workspace, com `PageHeader`, trilha e
seções em duas colunas responsivas. Confirmado em 2026-10-06. Não confirma o
destino do `UploadBaseSheet` atual, o menu de Conexões, nem os estados.

### Pergunta 2 (Interface) — destino do `UploadBaseSheet`

1. Substituir: botão do Workspace leva à página nova; `UploadBaseSheet`
   removido; "Usar base preparada" vira opção na etapa Arquivos
   (recomendado).
2. Manter os dois caminhos (envio rápido e avançado).
3. Substituir o envio, manter "Usar base preparada" como botão separado.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: o botão do Workspace passa a abrir a
página com etapas e o `UploadBaseSheet` é removido; não existe mais envio com
execução completa imediata. "Usar base preparada" passa a ser uma opção da
etapa Arquivos. Confirmado em 2026-10-06. Consequência: `INTERFACE.md`,
testes e consumidores do sheet precisam ser atualizados na spec.

### Pergunta 3 (Interface) — onde gerenciar conexões

1. Item de menu "Conexões" (owner/admin), lista em `DataGrid`, criação e
   edição em `Sheet`, como em Pessoas (recomendado).
2. Somente dentro da etapa Publicação.
3. Menu de gestão e atalho "Nova conexão" na etapa Publicação.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: novo item de menu "Conexões", visível
só a owner/admin; rota própria com `PageHeader`, trilha (Equipe → Conexões) e
`DataGrid` em largura total (coluna `ID`, nome, tipo, situação, linha
clicável para detalhe, ações independentes de editar, desativar/reativar e
excluir); criação e edição em `Sheet`; chave nunca devolvida (campo vazio e
máscara na edição). `member` não vê o item e a URL direta é recusada.
Confirmado em 2026-10-06. Não confirma se existe tela de detalhe, nem como a
etapa Publicação escolhe a conexão.

### Pergunta 4 (Interface) — formulário da etapa Divisão

1. Poucos campos com padrões do `config.yaml`; avisar arquivos Q&A
   (recomendado).
2. Mesmos campos mais seção "Avançado" recolhida.
3. Configuração por arquivo, com padrão geral.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: a etapa Divisão tem splitter (`Select`:
Markdown por cabeçalhos ou recursivo por caracteres), tamanho de chunk e
overlap, pré-preenchidos com os padrões do `config.yaml`; validação em linha
(overlap menor que o tamanho, mínimo e máximo) com ajuda curta e erro
abaixo do campo. Documentos com `splitter: qa` no frontmatter mantêm o Q&A e
a tela lista quais arquivos ficam fora desses parâmetros. Sem seção avançada
nem configuração por arquivo. Confirmado em 2026-10-06. Os valores exatos de
mínimo e máximo continuam abertos para a spec, a partir do `config.yaml`.

### Pergunta 5 (Interface) — etapa Prévia

1. Resumo mais lista paginada de chunks, filtro por documento, somente
   leitura (recomendado).
2. Duas colunas: documentos e chunks do documento selecionado.
3. Somente amostra dos primeiros chunks por documento.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: a Prévia mostra, no topo, contagens
(documentos, chunks, tamanho médio) e avisos; abaixo, lista paginada de
chunks com documento de origem, posição, tamanho e texto truncado com "ver
mais", e filtro por documento. É somente leitura; ajustar significa voltar à
etapa Divisão. Confirmado em 2026-10-06. Estados (cálculo em andamento,
vazio, erro) e limite de tamanho de lote ficam para a próxima rodada.

### Pergunta 6 (Interface) — etapa Publicação

1. Seleção das conexões ativas (embeddings e Qdrant), campo de coleção,
   resumo final e "Publicar" bloqueado por divergência de dimensão ou conexão
   desativada; leva à Base com `PainelProgresso` (recomendado).
2. Igual à 1, com "Testar conexão".
3. Publicação direta, sem resumo.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: a etapa Publicação oferece dois `Select`
de conexão (embeddings e Qdrant, só as ativas), a comparação de dimensões em
linha e o campo de coleção. Um resumo final lista arquivos, chunks, modelo,
coleção e destino. "Publicar" fica desabilitado enquanto houver divergência
de dimensão ou conexão desativada, com a razão visível. Ao publicar, leva à
página da Base com o `PainelProgresso` (inseridos, mantidos, removidos).
Sem "Testar conexão" nesta entrega. Confirmado em 2026-10-06. Sem conexão
ativa cadastrada, a etapa precisa orientar para "Conexões" (estado a detalhar).

### Pergunta 7 (Interface) — saída e retorno no fluxo

1. Nada guardado no servidor até publicar; voltar entre etapas preserva o
   preenchido; sair/recarregar descarta, com aviso antes de sair
   (recomendado).
2. Rascunho no servidor, retomável pela lista de Bases.
3. Rascunho local da configuração em `sessionStorage`, sem os arquivos.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: nenhum dado do fluxo é persistido no
servidor antes de publicar. Voltar entre etapas preserva o preenchimento e os
arquivos selecionados (em memória do navegador); sair ou recarregar descarta
tudo, e a tela avisa antes de sair com alterações pendentes. Confirmado em
2026-10-06. Não há estado "rascunho" de Base. Pendência técnica para a spec:
a prévia é calculada pelo backend sem gravar (os arquivos são enviados a cada
cálculo ou por um envio temporário descartável) — decidir sem criar estado
persistente, conforme limite de tamanho e retenção temporária.

### Pergunta 8 (Interface) — estados e acessibilidade

1. Conjunto completo: loading, vazio, erro, permissão, teclado e responsivo
   (recomendado).
2. Só o essencial: loading, erro e permissão.
3. Completo, mais conferência visual registrada por tarefa.
4. Escrever outra resposta. 5. Gere outras opções. 6. Avançar.
Resposta literal: “1”. Normalização: o fluxo e a tela de Conexões cobrem
- loading: prévia e publicação com `Button loading` e
  `IndicadorProcessamento`;
- vazio: sem conexão ativa, a Publicação orienta para "Conexões"; sem
  arquivos, "Próxima" desabilitada;
- erro: erro de campo abaixo do campo em vermelho, foco no primeiro erro;
  falha de prévia ou publicação em `Alert` com "Tentar novamente", sem perder
  o preenchimento;
- permissão: `member` não vê "Conexões" nem o botão de envio; URL direta
  recusada;
- teclado: etapas navegáveis, foco no título da etapa ao trocar, lista de
  chunks acessível, resultado anunciado por `aria-live`;
- responsivo: uma coluna no mobile.
Confirmado em 2026-10-06. A revisão visual (`VISUAL`) já é obrigatória por
tarefa pelo contrato central, sem depender desta decisão.

### Síntese da área Interface — 2026-10-06

Limite de oito perguntas atingido. Decidido: página com etapas (Arquivos →
Divisão → Prévia → Publicação) substituindo o `UploadBaseSheet`; "Usar base
preparada" na etapa Arquivos; menu "Conexões" (owner/admin) com `DataGrid` e
`Sheet`; Divisão com splitter, tamanho e overlap e aviso Q&A; Prévia com
resumo e lista paginada somente leitura; Publicação com conexões ativas,
dimensões em linha, resumo e botão bloqueado com razão; nada persistido
antes de publicar; estados e acessibilidade completos.

Lacunas abertas de Interface: tela de detalhe de conexão (existe ou não),
mínimos e máximos exatos de chunk e overlap, tamanho máximo de lote e
retenção temporária da prévia, comportamento da etapa Arquivos com "Usar
base preparada", e adicionar envios a uma Base existente.

Próximo passo: o item segue em Refining; ainda restam lacunas de Dados
(Workspace/Base/loader, precedência, auditoria). Registro e commit pendentes.

## Promoção — 2026-10-06

Promovido a `specs/planned/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md`
(SPEC-0026), em `Draft` com `Definition Gate: Pending`. Este item preserva a
proveniência e deixa de governar o comportamento. Lacunas ainda abertas, não
perguntadas por limite de oito perguntas por área, ficaram registradas como
`Pendente` na seção 2 da spec: auditoria das alterações em conexões, guarda e
rotação da chave de cifra em produção e confirmação dos limites numéricos.

### Fechamento das pendências da spec — 2026-10-06

Rodada de três perguntas pedida após a promoção; respostas literais “1”,
normalizadas assim:

- Auditoria: histórico próprio `eventos_conexao` (pessoa, ação, horário, sem a
  chave), retenção de 90 dias.
- Chave de cifra: única, fornecida como secret do Docker Swarm ou variável de
  ambiente, sem rotação automática; trocar exige recadastrar as conexões.
- Limites: tamanho de 200 a 4000; overlap de 0 até a metade do tamanho e
  sempre menor que o tamanho.

Incorporadas à SPEC-0026 (FR-002, FR-004, FR-006, DEC-011 a DEC-013).
