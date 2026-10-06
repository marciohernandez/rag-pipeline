# Backlog: Fluxo completo de ingestão inspirado nos Document Stores do Flowise

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0025 |
| Status | Refining |
| Produto | RAG Pipeline |
| Épico | A esclarecer |
| Funcionalidade | Preparação e indexação de documentos |
| Tipo | Melhoria |
| Prioridade | Terceira na ordem confirmada: corrigir exclusão, indicadores de processamento, fluxo de ingestão |
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
   owner/admin da mesma equipe e projeto, em qualquer Workspace. Gestão,
   campos e permissões de gestão ainda precisam de descoberta. O ciclo de
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
Resposta pendente. A reutilização por owner/admin já está confirmada e não
será perguntada novamente.
