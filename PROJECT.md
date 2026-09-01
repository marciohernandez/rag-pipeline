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
- sincronizar com Qdrant em modo espelho e suportar ChromaDB e Pinecone;
- aplicar uma política fail-closed antes de qualquer mutação remota,
  bloqueando opção destrutiva, modo incompatível, escopo ambíguo e remoção
  não confirmada pelo destino;
- executar busca semântica e um chat RAG simples por linha de comando.

## Limites

- processa atualmente arquivos `.md` diretamente na pasta configurada, sem a
  ingestão multi-formato prevista para o projeto-mãe;
- não executa a curadoria cruzada, detecção de contradições ou loop de feedback
  humano definidos para a V1 do `rag-pipeline`;
- não oferece API FastAPI, dashboard Next.js, autenticação, roles ou isolamento
  multi-tenant;
- não substitui o projeto-mãe nem antecipa suas funcionalidades de V1;
- operações remotas destrutivas, incluindo recriação de coleção, exigem
  decisão explícita fora do fluxo normal de sincronização.

## Contexto técnico

Aplicação Python 3.12+ gerenciada por `uv`, baseada em LangChain, Pytest e
integrações com Qdrant, ChromaDB, Pinecone e providers de embeddings. A
configuração não sensível fica em `config.yaml`; credenciais ficam fora do
repositório. Detalhes verificáveis permanecem em `.specsfy/STACK.md` e
`.specsfy/DATABASE.md`.

Como orientação futura de integração, a constituição 1.2.1 do `rag-pipeline`
define LangGraph/LangChain-first para orquestração de IA, modularidade,
encapsulamento, configuração centralizada, desenvolvimento orientado por specs,
testes Pytest e extensibilidade por providers. Essas regras não transformam a
stack futura do projeto-mãe em dependência já implementada neste componente.
