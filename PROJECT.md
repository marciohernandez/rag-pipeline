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
autenticação por token estático de demonstração e isolamento por tenant,
projeto e papel — mas ainda não há interface web nem acesso direto de
clientes externos neste repositório; o consumidor previsto é o frontend da
fatia 3, ainda não implementado.

## Capacidades principais

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
  base Markdown por upload ou base preparada, agenda o processamento como
  tarefa assíncrona (Procrastinate sobre PostgreSQL) sem bloquear a
  requisição, persiste estado/etapa/contagens/erro de cada execução, permite
  repetir uma execução falhada e apagar uma base (removendo arquivos,
  execuções, consultas, chunks e vetores associados), e responde consultas de
  validação sobre a base indexada — tudo isolado por tenant, projeto e papel
  (owner/admin/member) por trás de um token estático de demonstração.

## Limites

- processa atualmente arquivos `.md` diretamente na pasta configurada, sem a
  ingestão multi-formato prevista para o projeto-mãe;
- não executa a curadoria cruzada, detecção de contradições ou loop de feedback
  humano definidos para a V1 do `rag-pipeline`;
- não oferece dashboard Next.js; a fatia 2 (SPEC-0012) entrega um backend
  FastAPI com autenticação por token estático de demonstração (não é o
  modelo final) e persistência de tenant/projeto/papel em `src/app/`, mas
  cadastro, convite e login real de usuários continuam fora de escopo;
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
autenticação por token estático (`src/app/auth.py`); os routers em
`src/app/routers/` concentram os endpoints HTTP e não fazem outra leitura de
ambiente.

Como orientação futura de integração, a constituição 1.2.1 do `rag-pipeline`
define LangGraph/LangChain-first para orquestração de IA, modularidade,
encapsulamento, configuração centralizada, desenvolvimento orientado por specs,
testes Pytest e extensibilidade por providers. Essas regras não transformam a
stack futura do projeto-mãe em dependência já implementada neste componente.
