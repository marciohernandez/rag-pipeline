# Banco de dados

Mapa de persistência do pipeline Python. Não inclui schemas internos de
dependências instaladas em `.venv`, pois eles pertencem aos fornecedores e não
ao domínio deste repositório.

## Fontes de dados

<!-- specsfy:database:start -->
| Fonte | Tecnologia/forma | Evidência |
| --- | --- | --- |
| Documentos de entrada | Arquivos Markdown com frontmatter YAML | `config.yaml`, `src/loader.py` |
| Auditoria de chunks | Arquivo JSON local | `config.yaml`, `src/exporter.py` |
| Manifesto de sincronização | Arquivo JSON local | `pipeline.py`, `src/manifest.py` |
| Banco vetorial principal | Collection Qdrant remota, configurada sem credenciais no código | `config.yaml`, `src/embedder.py` |
| Banco vetorial alternativo | Collection ChromaDB local | `config.yaml`, `src/embedder.py` |
| Banco vetorial alternativo | Índice e namespace Pinecone remotos | `config.yaml`, `src/embedder.py` |

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações | Fonte |
| --- | --- | --- | --- | --- |
| Documento Markdown | Arquivo de origem | `page_content`, frontmatter (`document_id`, `tenant_id`, `type`, `version`, `status`, `splitter`), `nome_arquivo`, `caminho_relativo`, `source_hash` | Origina um `document_id` e vários chunks | `src/loader.py`, `src/identity.py` |
| Chunk auditável | Item de `chunks.json` | `chunk_index`, `nome_arquivo`, `total_chunks`, `metadata`, `content`, `content_length` | Pertence a um documento; usa `chunk_id`, `document_id`, `project_id` e `tenant_id` opcional | `src/exporter.py`, `src/identity.py` |
| Manifesto de execução | Objeto JSON | `run_id`, `generated_at`, `project_id`, `collection_name`, embedding, contagens, documentos, `chunk_ids`, `excluded_by_status_count` | Consolida documentos e chunks esperados antes da indexação; conta exclusões por status | `src/manifest.py`, `src/status_gate.py` |
| Ponto Qdrant | Vetor + payload | ID=`chunk_id`, vetor configurado, `page_content`, `metadata` (inclui `tenant_id`, `type`, `version` quando presentes) | Escopo lógico por `metadata.project_id` + `metadata.tenant_id` quando declarado; documento por `metadata.document_id` | `src/embedder.py` |
| Collection ChromaDB | Collection gerenciada pelo provider | Documento, embedding e metadados compatíveis com LangChain | Nome configurado; persistência no diretório local | `src/embedder.py`, `config.yaml` |
| Vetor Pinecone | Vetor + metadados | ID estável derivado de namespace, caminho e posição; conteúdo e metadados LangChain | Isolado por índice e namespace | `src/embedder.py`, `config.yaml` |
<!-- specsfy:database:end -->

## Decisões, ownership e retenção

- A pasta Markdown configurada é a fonte de verdade da execução local.
- No Qdrant, `sync_mode: mirror` exige conjunto esperado não vazio e escopo com
  um único `project_id` antes de tocar o destino. Depois de concluir todos os
  upserts, o pipeline relê o mesmo escopo e confirma a presença de cada
  `chunk_id` esperado; somente então remove IDs obsoletos daquele `project_id`.
  Uma substituição total dos IDs anteriores permanece permitida quando todos os
  novos IDs estiverem confirmados.
- Identidades de documentos e chunks são determinísticas; `run_id` identifica
  apenas a execução do manifesto. `document_id` recebido no frontmatter (do
  `rag-pipeline`) prevalece sobre a geração determinística local; na ausência
  dele, a geração local é mantida.
- `tenant_id` é opcional no frontmatter. Quando presente em qualquer documento
  do lote de sincronização, a totalidade do lote precisa declará-lo com o
  mesmo valor; o escopo lógico de leitura e remoção em modo espelho passa a
  ser `project_id` + `tenant_id`, isolando a limpeza de obsoletos entre
  tenants que compartilham o mesmo `project_id`. Sem `tenant_id` no lote, o
  escopo continua sendo somente `project_id`, como antes do SPEC-0002.
- `status` presente em `config.yaml` (`contrato_markdown.status_bloqueado`)
  exclui o documento da indexação antes do chunking; a lista é vazia por
  padrão (fail-open) e não fixa valores do contrato ainda não publicado pelo
  `rag-pipeline`.
- `type` e `version` do frontmatter são gravados no payload de cada chunk como
  metadado de auditoria e consulta, sem participar da identidade, do
  chunking ou do bloqueio por status.
- O código atual não implementa tenant persistente com autenticação/permissões
  próprias — apenas o isolamento de escopo lógico descrito acima. A exigência
  multi-tenant completa do projeto-mãe é uma restrição futura de integração,
  não um schema já existente.
- O código atual ainda não implementa ownership e retenção multi-tenant. As
  regras confirmadas para a consolidação no projeto-mãe estão registradas em
  `Informações a guardar confirmadas` abaixo.

<!-- specsfy:conversation-data:start -->
## Informações a guardar confirmadas

| Informação | Para que serve | O que guardar | Formato sugerido | Ligações | Quem usa | Quando muda ou sai | Fontes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Base de documentos do projeto | Disponibilizar os documentos que serão processados, reprocessados e demonstrados no projeto ativo. | Arquivos Markdown, nome, origem por upload ou base preparada e identificação do projeto ativo. | Arquivos para os documentos e textos curtos para nome e origem. | Pertence ao tenant e ao projeto ativo; origina uma ou mais execuções, chunks e vetores. | Owner e admin podem enviar, administrar e apagar; member pode consultar sem apagar. | Permanece enquanto o projeto existir. Owner ou admin pode apagar quando precisar, mediante confirmação; a exclusão remove conteúdo, execuções, consultas, chunks e vetores associados e preserva somente um registro sem conteúdo de que a exclusão ocorreu. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
| Execução do pipeline | Acompanhar o processamento, comprovar o resultado e permitir auditoria e reexecução. | Base e origem usadas, situação e etapas, contagens, horários de início e término, erros e manifesto de auditoria. | Escolha entre situações para o estado, números para contagens, datas e horários para acontecimentos, texto para erros e registro de auditoria para o manifesto. | Pertence a uma base, a um tenant e a um projeto; liga documentos, chunks, vetores e consultas de validação. | Owner e admin podem iniciar, repetir, consultar e administrar; member pode acompanhar e consultar, sem apagar. | Permanece com a base enquanto o projeto existir e é removida com seu conteúdo quando owner ou admin apaga a base, preservando somente o registro mínimo da exclusão. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
| Consulta de validação da recuperação | Demonstrar e auditar o que foi recuperado da base indexada. | Pergunta realizada, resultado recuperado, chunks-fontes apresentados e horário da consulta. | Texto para pergunta e resultado, lista de referências para chunks-fontes e data e horário para a consulta. | Pertence ao tenant, ao projeto, à base consultada e à execução que produziu a indexação. | Owner, admin e member podem realizar e consultar; somente owner e admin administram o histórico por meio da base. | Permanece com a base enquanto o projeto existir e é removida quando owner ou admin apaga a base, preservando somente o registro mínimo da exclusão. | specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md; specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md |
<!-- specsfy:conversation-data:end -->
