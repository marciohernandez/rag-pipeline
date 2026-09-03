# Projeto

## História e motivação

Este repositório nasceu como um pipeline Python independente para preparar
documentos Markdown para RAG. Ele é o primeiro componente que será finalizado
antes da montagem do projeto-mãe `rag-pipeline`, ainda em estágio inicial.

O projeto-mãe trata da ingestão multi-formato, extração, curadoria e validação
humana de bases de conhecimento. Na V1, ele entrega Markdown validado e deixa
chunking, embeddings e indexação fora do seu escopo. Este componente cobre
justamente essa etapa posterior e deve permanecer integrável à evolução V2.

## Finalidade

Transformar documentos Markdown estruturados em chunks rastreáveis, gerar
embeddings, sincronizar os pontos com um banco vetorial e permitir a validação
da recuperação. O resultado principal é uma coleção vetorial auditável,
idempotente e pronta para consumo por sistemas RAG.

## Pessoas e contexto de uso

Na fase atual, Marcio e sua equipe de consultoria operam o pipeline por linha
de comando durante a preparação e validação técnica de bases de conhecimento.
Não há interface web, autenticação ou acesso direto de clientes neste
repositório.

## Capacidades principais

- carregar arquivos Markdown e extrair frontmatter YAML;
- dividir conteúdo respeitando a hierarquia de títulos e limites configurados;
- gerar chunks detalhados e resumos de seções elegíveis;
- atribuir identidades e hashes estáveis a documentos e chunks;
- produzir `chunks.json` e manifesto local para auditoria;
- gerar embeddings por providers configuráveis;
- trocar ou adicionar provider de embeddings e de banco vetorial sem alterar o
  pipeline nem os CLIs: desde a SPEC-0003 eles são plugins atrás de contratos
  neutros, criados por uma factory a partir do nome declarado em `config.yaml`;
- sincronizar com Qdrant em modo espelho e suportar ChromaDB e Pinecone;
- publicar contagens exatas de `previstos`, `inseridos`, `mantidos` e
  `removidos` em qualquer backend suportado, inclusive nos que operam em
  `append`;
- recuperar somente dentro do escopo lógico autorizado: `project_id` é
  obrigatório e `tenant_id` é explícito, de modo que omiti-lo alcança apenas os
  registros sem tenant em vez de consultar sem filtro;
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
- validar uma base já indexada sem alterá-la, por um comando único somente
  leitura que confere o escopo no destino, compara as identidades do manifesto
  com as indexadas e executa um gabarito de consultas versionado junto da base.
  O veredito distingue base aprovada, base reprovada e ambiente que não pôde ser
  validado, e fica gravado em resultado estruturado para consumo posterior.

## Limites

- processa atualmente arquivos `.md` diretamente na pasta configurada, sem a
  ingestão multi-formato prevista para o projeto-mãe;
- não executa a curadoria cruzada, detecção de contradições ou loop de feedback
  humano definidos para a V1 do `rag-pipeline`;
- não oferece API FastAPI, dashboard Next.js, autenticação, roles ou
  persistência multi-tenant com ownership próprio; o isolamento hoje
  disponível é apenas o escopo lógico de sincronização por `tenant_id`;
- não substitui o projeto-mãe nem antecipa suas funcionalidades de V1;
- operações remotas destrutivas, incluindo recriação de coleção, exigem
  decisão explícita fora do fluxo normal de sincronização;
- a validação da recuperação comprova o comportamento de uma base contra o
  gabarito declarado para ela; ela não julga a qualidade das respostas de uma
  aplicação RAG nem substitui avaliação humana do conteúdo.

## Contexto técnico

Aplicação Python 3.12+ gerenciada por `uv`, baseada em LangChain, Pytest e
integrações com Qdrant, ChromaDB, Pinecone e providers de embeddings. A
configuração não sensível fica em `config.yaml`; credenciais ficam fora do
repositório. Detalhes verificáveis permanecem em `.specsfy/STACK.md` e
`.specsfy/DATABASE.md`.

Desde a SPEC-0003 a fronteira técnica é explícita: `src/providers/` concentra
os contratos neutros, a factory e os adapters, e é o único lugar do repositório
onde SDK de banco vetorial ou classe de embeddings pode ser importado — regra
verificada por um teste estático de AST. `src/indexing.py` é o serviço de
aplicação que traduz `config.yaml` e chunks para esses contratos, e
`src/safety.py` mantém a política fail-closed antes de qualquer composição de
provider. `src/validation.py` concentra o caso de uso de validação somente
leitura e é chamável sem a camada de linha de comando; `validate.py` apenas o
expõe ao operador. O antigo `src/embedder.py`, que concentrava fábricas, clientes,
sincronização e leitura, foi removido sem shim.

Como orientação futura de integração, a constituição 1.2.1 do `rag-pipeline`
define LangGraph/LangChain-first para orquestração de IA, modularidade,
encapsulamento, configuração centralizada, desenvolvimento orientado por specs,
testes Pytest e extensibilidade por providers. Essas regras não transformam a
stack futura do projeto-mãe em dependência já implementada neste componente.
