# Projeto

## História e motivação

**Este repositório é agora o `rag-pipeline`, consolidando ambas as fases:
- Fase 1: ingestão multi-formato, extração, curadoria e geração de Markdown
- Fase 2: chunking, embeddings, indexação vetorial e validação de recuperação**

Antes, havia separação entre `rag-pipeline` (projeto-mãe em estágio inicial) e `rag-ingestion-pipeline` (segunda fase apenas). A decisão de integrar ambas em um único repositório modular simplifica a stack, evita duplicação de dependências (Python, LangChain, pytest, etc.) e facilita testes end-to-end.

Na V1, a Fase 1 entreg  a Markdown validado com frontmatter YAML. A Fase 2 recebe esse Markdown e o transforma em coleções vetoriais auditáveis, idempotentes e prontas para consumo por sistemas RAG.

## Finalidade

Transformar documentos Markdown estruturados em chunks rastreáveis, gerar
embeddings, sincronizar os pontos com um banco vetorial e permitir a validação
da recuperação. O resultado principal é uma coleção vetorial auditável,
idempotente e pronta para consumo por sistemas RAG.

## Pessoas e contexto de uso

Na fase atual, Marcio e sua equipe de consultoria operam o pipeline por linha
de comando durante a preparação e validação técnica de bases de conhecimento.
Desde a SPEC-0012, um backend HTTP (`src/app/`) também está disponível, com
isolamento por tenant, projeto e papel. A SPEC-0013 (fatia 3) acrescentou um
frontend demonstrável em `frontend/` (Next.js, projeto Node autocontido).
Desde a SPEC-0020, cada pessoa entra com e-mail e senha, usa uma sessão
revogável e é reconhecida como autora das ações. Marcio conduz a jornada
completa — enviar ou escolher uma base
Markdown, acompanhar o processamento assíncrono, consultar a base indexada e
ver os chunks-fontes — sem tocar terminal, CLI ou chamada HTTP manual.
O cadastro aberto deixou de ser necessário: owners e admins fazem a gestão
básica das Pessoas do próprio tenant — criam, listam, corrigem nome/e-mail,
alteram papéis dentro da própria autoridade, desativam, reativam e redefinem
senhas. Convite por e-mail, recuperação autônoma por link, SSO e uma mesma
Pessoa vinculada a mais de um tenant ou projeto continuam fora de escopo.

Com a SPEC-0019, a equipe organiza as Bases em Workspaces antes do envio,
escolhe opcionalmente a coleção vetorial de cada Base e informa metadados
livres de rótulo/valor para seus chunks. A navegação demonstrável parte da
lista de Workspaces e mantém as permissões dos papéis existentes.

Com a SPEC-0026, owner e admin deixam de enviar e executar de uma só vez:
cadastram conexões reutilizáveis de embeddings OpenAI e de Qdrant (chave somente
escrita e cifrada, histórico de alterações) e conduzem a nova Base em quatro
etapas — Arquivos, Divisão, Prévia e Publicação. Escolhem estratégia, tamanho
e overlap dos chunks, revisam os chunks sem gravar nada, escolhem as conexões
e a coleção e publicam, com bloqueio quando a dimensão do modelo difere da da
coleção. Member continua só consultando.

Com a SPEC-0029, as configurações do processamento que ficavam presas no
backend passam a ser escolhidas no próprio fluxo de Nova Base: seis
estratégias de divisão do `langchain-text-splitters` aplicáveis a Markdown,
cada uma com seus campos, resumos de seção, níveis de cabeçalho, mínimo útil
de qualidade, status bloqueados, `batch_size` e `sync_mode`. A Prévia permite
escolher quantos chunks ver por página, e cada conexão é testada ao ser salva,
sem expor a chave. A Base guarda o que foi usado, e Bases anteriores não mudam.

Com a SPEC-0030, a unidade do Workspace deixa de ser a Base e passa a ser a
Coleção: o nome é dado no primeiro envio e os envios seguintes acumulam
documentos nela. Cada documento tem identidade estável (coleção + nome do
arquivo, ou o `document_id` do frontmatter), de modo que reenviar um arquivo
idêntico não duplica nem gera embedding, e reenviar um arquivo com conteúdo novo
substitui a versão anterior sem tocar outros documentos. A Coleção guarda
conexões fixas e um nome físico imutável no Qdrant, igual ao nome digitado na criação (a exclusão física só vale para coleção registrada pelo app); o `sync_mode` sai da
interface. Como a identidade do chunk deixou de depender do hash do arquivo
inteiro nem da pasta temporária, a primeira sincronização da CLI depois dessa
mudança reindexa uma vez.

Com a SPEC-0034, o PostgreSQL ganha backup diário cifrado para um bucket R2
separado, retenção de 7 diários e 4 semanais, avisos de falha por e-mail e
chat e restauração somente em banco novo. O mecanismo é ensaiado no Docker
local antes da publicação; a conferência dos serviços reais acontece na VPS.

Com a SPEC-0035, o deploy manual em produção ganha o runbook `deploy/RUNBOOK.md`:
atualização, primeira instalação e emergências. Cada imagem passa a ser etiquetada
pelo commit, as três últimas versões ficam no nó e a volta atrás é um único comando
(`deploy/build_and_deploy.sh --versao <etiqueta>`).

## Capacidades principais

- converter páginas de PDF com conteúdo em imagem por OCR local, em português
  e inglês, preservando a ordem das páginas e o conteúdo de PDFs de texto
  (SPEC-0033); idioma, limite de páginas e mínimo de texto são configuráveis
  na seção `conversao` do `config.yaml`;

- escolher Claro, Escuro ou Sistema no menu da pessoa, com preferência por navegador, aplicação antes da primeira pintura e telas existentes acessíveis nos dois temas (SPEC-0024);

- administrar conexões reutilizáveis de ingestão e publicar uma Base em etapas
  (SPEC-0026): prévia descartável dos chunks com estratégia, tamanho e overlap
  escolhidos por Base, conexões de embeddings e de Qdrant com chave cifrada,
  verificação de dimensão antes de gravar e parâmetros guardados na Base para
  repetir a execução; desde a SPEC-0029, também estratégia entre seis
  divisores, resumos, cabeçalhos, qualidade e destino escolhidos por Base, e
  teste da conexão ao salvar;
- carregar arquivos Markdown e extrair frontmatter YAML;
- dividir conteúdo respeitando a hierarquia de títulos e limites configurados;
- gerar chunks detalhados e resumos de seções elegíveis;
- atribuir identidades e hashes estáveis a documentos e chunks;
- produzir `chunks.json` e manifesto local para auditoria;
- publicar o relatório de qualidade da execução, legível e agrupado por
  documento, e gravar o resultado estruturado com o detalhe por chunk em
  arquivo próprio, separado do manifesto;
- gerar embeddings por providers configuráveis;
- trocar ou adicionar provider de embeddings e de banco vetorial sem alterar o
  pipeline nem os CLIs: desde a SPEC-0003 eles são plugins atrás de contratos
  neutros, criados por uma factory a partir do nome declarado em `config.yaml`;
- sincronizar com Qdrant em modo espelho, único provider concreto de vector
  store desde a SPEC-0010; a abstração multi-provider permanece aberta para
  novos destinos futuros;
- publicar contagens exatas de `previstos`, `inseridos`, `mantidos` e
  `removidos` em qualquer backend suportado, inclusive nos que operam em
  `append`;
- demonstrar a fatia funcional por um frontend web (`frontend/`, SPEC-0013,
  SPEC-0019 e SPEC-0020): login por pessoa, listagem de Workspaces do
  tenant/projeto ativo,
  Coleções agrupadas dentro de cada Workspace (SPEC-0030), envio por upload de
  `.md` ou base preparada para uma coleção nova ou existente, lista de
  documentos com painel de chunks, substituição e exclusão de documento,
  histórico de envios com detalhe, progresso, polling e repetição do que
  falhou, renomear e apagar coleção (apagar exige digitar o nome e remove a
  coleção física no Qdrant, owner/admin) e consulta à coleção inteira com os
  chunks-fontes;
- recuperar somente dentro do escopo lógico autorizado: `project_id` é
  obrigatório e `tenant_id` é explícito, de modo que omiti-lo alcança apenas os
  registros sem tenant em vez de consultar sem filtro;
- avaliar a qualidade da preparação entre o manifesto e a indexação, em dois
  níveis: seis invariantes determinísticos de integridade e rastreabilidade que
  interrompem a execução, e sinais heurísticos — perda de estrutura de títulos,
  truncamento de frase, duplicata exata, texto colapsado, conteúdo útil curto e
  distribuição de tamanho — que apenas relatam, agrupados por documento de
  origem;
- aplicar uma política fail-closed antes de qualquer mutação remota,
  bloqueando opção destrutiva, modo incompatível, escopo ambíguo e remoção
  não confirmada pelo destino;
- receber identidade (`document_id`), escopo por tenant (`tenant_id`),
  bloqueio por status e metadado auditável (`type`, `version`) do frontmatter
  enviado pelo `rag-pipeline`, isolando a sincronização por tenant no mesmo
  `project_id` quando declarado;
- dividir documentos no formato pergunta-e-resposta do projeto-mãe por blocos
  `++++`, preservando cada par íntegro em um chunk;
- executar busca semântica e um chat RAG simples por linha de comando;
- derivar das chaves `projeto.nome` e `projeto.descricao` a identidade exibida
  pelas ferramentas operacionais, sem manter cliente ou domínio fixo no código;
- validar uma base já indexada sem alterá-la, por um comando único somente
  leitura que confere o escopo no destino, compara as identidades do manifesto
  com as indexadas e executa um gabarito de consultas versionado junto da base.
  O veredito distingue base aprovada, base reprovada e ambiente que não pôde ser
  validado, e fica gravado em resultado estruturado para consumo posterior.
- expor um backend de aplicação FastAPI (`src/app/`, SPEC-0012) que recebe uma
  base Markdown por upload ou base preparada como envio para uma Coleção,
  agenda o processamento como tarefa assíncrona (Procrastinate sobre
  PostgreSQL, um envio por vez em cada coleção) sem bloquear a requisição,
  persiste estado/etapa/contagens/erro de cada envio, permite repetir um envio
  que falhou, apagar um documento (só os chunks dele) ou a coleção inteira
  (arquivos, envios, consultas e a coleção física no Qdrant), e responde
  consultas sobre a coleção — tudo isolado por tenant, projeto e papel
  (owner/admin/member) por uma sessão revogável de pessoa. Cada Coleção
  pertence a um Workspace, guarda conexões e dimensão fixas e tem um nome físico
  imutável no Qdrant; os pares de metadados informados no envio seguem para
  seus chunks;
- deixar rastro diagnosticável de uma execução que falha: quem opera encontra
  no log do worker o tipo da exceção, a etapa alcançada e o ponto do código,
  enquanto quem usa continua vendo apenas uma mensagem segura, sem detalhe de
  provedor nem credencial;
- operar os secrets de produção do Swarm por um script de linha de comando
  (`deploy/secrets.sh`, SPEC-0027): criar os secrets sem expor valores, conferir
  se todos existem antes de cada deploy, trocar um secret criando uma nova
  versão e bloquear por padrão as trocas de `postgres_password` e de
  `conexoes_chave`, que têm efeito colateral; o ensaio local usa o mesmo
  mecanismo com valores fictícios;
- orientar quem usa o sistema por um assistente especialista em RAG e em cada
  etapa do pipeline (SPEC-0021): um botão global abre um painel de chat em
  qualquer tela autenticada, com histórico por Pessoa, respostas ancoradas na
  documentação viva do produto (indexada por `index_assistant_docs.py`) com
  fontes citadas e, opcionalmente, a análise de uma Coleção do próprio escopo;
- o assistente evolui para um copilot com acesso ao sistema e ao conteúdo
  processado (SPEC-0031): sem escolher coleção, ele busca nos trechos indexados
  de todas as coleções do tenant e projeto da Pessoa, consulta o estado
  operacional (coleções, documentos, envios, falhas e configurações) e o
  conteúdo processado que o worker guarda de cada documento (texto convertido e
  trechos com etiquetas), responde com fontes clicáveis para a coleção, o
  documento ou o envio e sugere o passo com o link da tela, sempre sem executar
  ação. O seletor de coleção vira um filtro opcional; conexão e divisão ficam
  restritas a admin e credenciais nunca chegam ao modelo, à resposta nem aos
  logs.

## Limites

- o pipeline de indexação (`src/pipeline/loader.py`) continua lendo apenas
  arquivos `.md` diretamente na pasta configurada; a SPEC-0023 entrega a
  ingestão multi-formato prevista para o projeto-mãe como uma capacidade
  própria — conversão de PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX, HTML e imagem (OCR) em
  Markdown por lote, em `src/pipeline/conversion/` e
  `POST /api/v1/conversoes` — sem criar nem alterar uma Base: quem usa baixa o
  `.md` gerado e decide se e quando enviá-lo como Base. A lista da aba mostra
  um documento por linha, com a situação em português, e quem tem permissão de
  escrita pode apagar um documento convertido ou que falhou (original, `.md` e
  registro), mas não um que ainda está na fila ou processando;
- não executa a curadoria cruzada, detecção de contradições ou loop de feedback
  humano definidos para a V1 do `rag-pipeline`;
- a fatia 2 (SPEC-0012) entregou o backend FastAPI e a SPEC-0020 substituiu a
  autenticação estática por Pessoas, senhas Argon2id e sessões revogáveis, com persistência de
  tenant/projeto/papel em `src/app/`; a fatia 3 (SPEC-0013) entrega o
  frontend `frontend/` que consome esse backend para a jornada demonstrável.
  A SPEC-0019 organiza essa jornada por Workspace sem criar autenticação real;
  a Coleção pertence a um Workspace, e a interface não oferece mover uma
  Coleção ou um documento entre Workspaces nem entre coleções. Migrar Bases,
  execuções ou consultas antigas também ficou fora: o comando
  `python -m src.app.descartar_bases` as apaga.
  Não há cadastro aberto: a gestão básica de Pessoas acontece na aplicação e o
  primeiro owner nasce pelo comando de implantação. Convite/envio de e-mail,
  recuperação autônoma de senha por link, SSO e múltiplos tenants ou projetos
  por Pessoa continuam fora de escopo; o frontend roda localmente (`next dev`
  + backend FastAPI local) e deploy fica fora de escopo da SPEC-0013;
- o assistente apenas orienta: não tem ferramentas, não cria, altera nem apaga
  Workspace, Coleção, envio ou configuração, e só conversa sobre o produto e o
  conteúdo dos documentos da Pessoa (recusa outros assuntos). O conteúdo
  processado só existe para documentos enviados depois da SPEC-0031. Memória de longo prazo entre conversas, streaming, anexos,
  compartilhamento de conversas e limite de taxa ficam fora desta entrega; o
  conteúdo da conversa sai para o provedor de LLM configurado (OpenRouter);
- não substitui o projeto-mãe nem antecipa suas funcionalidades de V1;
- operações remotas destrutivas, incluindo recriação de coleção, exigem
  decisão explícita fora do fluxo normal de sincronização;
- a validação da recuperação comprova o comportamento de uma base contra o
  gabarito declarado para ela; ela não julga a qualidade das respostas de uma
  aplicação RAG nem substitui avaliação humana do conteúdo.

## Contexto técnico

Aplicação Python 3.12+ gerenciada por `uv`, baseada em LangChain, Pytest e
integração com Qdrant e providers de embeddings. A
configuração não sensível fica no `config.yaml` local, criado a partir do
`config.example.yaml` neutro e versionado; credenciais ficam fora do
repositório. Detalhes verificáveis permanecem em `.specsfy/STACK.md` e
`.specsfy/DATABASE.md`. Ruff 0.16.5 e Pytest são reproduzíveis localmente, e o
workflow GitHub Actions executa os mesmos gates em cada push e pull request sem
receber segredos do projeto.

Desde a SPEC-0003 a fronteira técnica é explícita: `src/pipeline/providers/` concentra
os contratos neutros, a factory e os adapters, e é o único lugar do repositório
onde SDK de banco vetorial ou classe de embeddings pode ser importado — regra
verificada por um teste estático de AST. `src/pipeline/indexing.py` é o serviço de
aplicação que traduz `config.yaml` e chunks para esses contratos, e
`src/pipeline/safety.py` mantém a política fail-closed antes de qualquer composição de
provider. `src/pipeline/validation.py` concentra o caso de uso de validação somente
leitura e é chamável sem a camada de linha de comando; `validate.py` apenas o
expõe ao operador. O antigo `src/embedder.py`, que concentrava fábricas, clientes,
sincronização e leitura, foi removido sem shim.

Desde a SPEC-0008, `src/pipeline/service.py` é a fachada síncrona e estável dos
casos de uso de preparação, sincronização, validação e consulta. A camada de
backend vive em `src/app/` e pode importar somente essa fachada; um teste AST
verifica a fronteira nos dois sentidos. Os comandos da raiz continuam resolvendo
`config.yaml` e delegam operações à fachada sem mudar sua invocação. Desde a
SPEC-0012, `src/app/main.py` é o entrypoint FastAPI equivalente aos CLIs: único
ponto que lê variável de ambiente para resolver PostgreSQL (`src/app/db.py`,
`src/app/models.py`), a fila assíncrona Procrastinate (`src/app/tasks.py`), o
storage de arquivos (`src/app/storage.py`, Cloudflare R2 ou disco local) e a
autenticação por pessoa e sessão (`src/app/auth.py`, `src/app/accounts.py`);
os routers em
`src/app/routers/` concentram os endpoints HTTP e não fazem outra leitura de
ambiente.

Como orientação futura de integração, a constituição 1.2.1 do `rag-pipeline`
define LangGraph/LangChain-first para orquestração de IA, modularidade,
encapsulamento, configuração centralizada, desenvolvimento orientado por specs,
testes Pytest e extensibilidade por providers. Essas regras não transformam a
stack futura do projeto-mãe em dependência já implementada neste componente.

### Feedback local de processamento — SPEC-0025

Esperas visíveis de autenticação, Workspaces, Coleções, Pessoas, envios e
assistente mostram um círculo junto da ação ou área, mantendo controles
independentes disponíveis. Os indicadores acompanham sucesso, erro e
indexação ativa, respeitam tema e preferência por movimento reduzido.

A SPEC-0036 acrescenta entrada por URL pública na conversão: a API enfileira sem buscar a página, e o worker busca somente HTML em destinos públicos validados. O relatório registra a origem sem credenciais ou query string.

A SPEC-0037 acrescenta a limpeza de conteúdo de domínio ao lote de conversão: depois de convertidos, os documentos aguardam o resumo do domínio da empresa (proposto por IA quando permitido e confirmado por owner ou admin), recebem regras fixas contra ruído, avaliação opcional por IA com confiança (dúvida é mantida e marcada) e remoção de duplicidade entre documentos, com log de exclusões (texto removido por 30 dias) e relatório do lote (90 dias).

A SPEC-0038 acrescenta a análise de contradições por coleção: a pedido de owner ou admin, com aviso de envio à IA do Workspace, o sistema extrai afirmações dos `.md` já limpos, agrupa por assunto e julga só os pares do mesmo assunto, em partes, com progresso e retomada. O relatório (conflito, versão desatualizada, duplicado) abre numa rota própria da coleção, com download em Markdown e PDF, e é guardado por 90 dias. A análise só relata: nenhum documento é alterado.

A SPEC-0039 fecha o ciclo com a empresa: owner ou admin colam a resposta no relatório de contradições; a IA do Workspace, depois do aviso confirmado, propõe por contradição qual versão vale, marcando cada proposta como clara ou incerta (a contradição não coberta fica "Sem decisão"). Nada é gravado sem confirmação: as claras vêm num bloco com "Confirmar todas" e as incertas pedem Aceitar, Editar ou Manter sem decisão. A correção troca só o trecho alvo (localizado de forma determinística e conferido por hash), cria uma versão numerada do documento com a anterior preservada por 90 dias, publica o `.md` por um novo envio à coleção e registra a decisão (quem, quando, a resposta da empresa e a proposta). É possível voltar a uma versão antiga, reanalisar mostrando resolvidas e novas, e "Liberar para a base", que apenas marca a coleção como revisada, com aviso quando restam contradições abertas. Member só consulta.

A SPEC-0040 organiza imagens e tabelas na conversão: quando o lote tem duas ou mais imagens, o sistema propõe grupos e ordem usando só nome do arquivo, data e hora e pasta de origem (sem OCR e sem IA externa) e o lote fica "Aguardando grupos". Owner ou admin conferem, movem e reordenam as imagens e confirmam; só então cada grupo vira um `.md` com uma seção por imagem na ordem aprovada e a linha "Origem: <arquivo>" (imagem isolada vira documento próprio; imagem ilegível é sinalizada e o documento recebe "Revisar"). Tabelas simples saem como tabelas Markdown, as complexas viram texto corrido com "Revisar" e a tabela que continua na página seguinte é juntada quando as colunas batem. Member só consulta; as propostas expiram em 7 dias.

Planilhas com várias abas aguardam confirmação antes da conversão. Limites são configuráveis por documento e lote, com recusa parcial. Sinais determinísticos indicam leitura ruim; somente um pedido explícito por documento aciona IA externa, preservando o Markdown anterior quando a leitura falha.
