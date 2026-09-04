# Aplicação e implementações

<!-- specsfy:documentator:start -->
## Superfícies

Categorias: Serviços, Rotas e APIs, Páginas, Componentes, Testes e Outras fontes.

Relação: relaciona cada arquivo observado à sua superfície.

| Categoria | Arquivo | Símbolos |
| --- | --- | --- |
| Outras fontes | — | Nenhum arquivo de código encontrado |
<!-- specsfy:documentator:end -->

## Inventário Python verificado

| Superfície | Arquivos | Responsabilidade |
| --- | --- | --- |
| Orquestração CLI | `pipeline.py` | Carregar, dividir, identificar, manifestar, exportar, avaliar a qualidade e indexar documentos, em cinco etapas. O gate de qualidade roda antes do desvio de `--only-chunks` e cancela a indexação com código 1 quando um invariante crítico falha. |
| Carga | `src/pipeline/loader.py` | Ler Markdown, frontmatter e hash de origem com modo estrito. |
| Chunking | `src/pipeline/chunker.py` | Dividir por títulos, caracteres ou blocos Q&A (`splitter: qa`) e gerar resumos de seção. |
| Identidade | `src/pipeline/identity.py` | Produzir IDs e hashes determinísticos de documentos e chunks; preserva `document_id` recebido do frontmatter quando presente. |
| Manifesto | `src/pipeline/manifest.py` | Construir, validar e exportar o manifesto da execução. |
| Exportação | `src/pipeline/exporter.py` | Gerar auditoria JSON e resumo dos chunks. |
| Contratos de provider | `src/pipeline/providers/contracts.py`, `errors.py`, `factory.py` | Definir tipos neutros, hierarquia de erros e o despacho de provider por nome. |
| Adapters de embeddings | `src/pipeline/providers/embeddings/` | OpenAI, OpenRouter, Hugging Face e um fake determinístico, com cliente lazy. |
| Adapters de vector store | `src/pipeline/providers/vectorstores/` | Qdrant (único provider concreto desde a SPEC-0010) e in-memory (oráculo); `base.py` orquestra a sincronização e emite as contagens. A `ProviderFactory` continua extensível para novos providers. |
| Serviço de indexação | `src/pipeline/indexing.py` | Traduzir `config.yaml` e chunks para os contratos, indexar e recuperar sob a política de segurança. |
| Validação de recuperação | `src/pipeline/validation.py` | Validar localmente o gabarito de consultas antes de qualquer acesso ao destino; a conferência remota e a apresentação CLI são entregues pela SPEC-0004 em progresso. |
| Gate de qualidade | `src/pipeline/quality.py` | Avaliar o conjunto local antes da indexação em dois níveis: seis invariantes determinísticos que interrompem por `QualityGateError` e sinais heurísticos que apenas relatam. O invariante de contagem do manifesto só é avaliado quando há manifesto. Deriva o limite máximo de tamanho do `chunk_size` efetivo de cada documento, somada a margem do breadcrumb, e aplica um mínimo configurável medido sobre o conteúdo útil. Calcula seis sinais heurísticos — perda de estrutura, truncamento de frase, duplicata exata, texto colapsado, conteúdo útil curto e tamanho acima do máximo — mais a distribuição por `chunk_type`, todos agrupados por documento de origem. Publica o relatório legível por `render()` e grava o resultado estruturado em `output/<base>/quality-<uuid>.json`, com o detalhe por chunk, sem tocar o `manifest.json`. Entregue pela SPEC-0006. |
| Segurança de sincronização | `src/pipeline/safety.py` | Aplicar as guardas fail-closed de opção destrutiva, modo, escopo (project_id + tenant_id) e remoção. |
| Contrato de frontmatter | `src/pipeline/status_gate.py` | Excluir documentos com status presente na lista bloqueante configurável, com registro auditável. |
| Configuração | `src/pipeline/config.py`, `config.yaml` | Carregar configuração não sensível, ambiente e logging. |
| Consulta | `search.py`, `chat.py`, `demo_rag.py` | Busca e demonstrações RAG por linha de comando. |
| Importação auditada | `upsert_from_chunks.py` | Validar chunks contra manifesto e enviar ao destino vetorial. |
| Diagnóstico de qualidade | `quality.py`, `src/pipeline/quality.py` | Avaliar um arquivo de chunks já gerado sem abrir conexão com o destino: relatório legível no stdout, resultado estruturado em arquivo próprio e códigos 0 aprovado, 1 reprovado e 2 quando não foi possível avaliar. Sem manifesto neste modo, o invariante de contagem é pulado e o salto é declarado. |
| Validação | `validate.py`, `src/pipeline/validation.py` | Conferir, sem alterar o destino, conexão e escopo, correspondência entre manifesto e identidades indexadas e o comportamento de recuperação declarado no gabarito da base. Encerra com 0 aprovado, 1 reprovado e 2 quando não foi possível validar. |
| Backend de aplicação — entrypoint | `src/app/main.py` | Único ponto que lê variável de ambiente; monta FastAPI, injeta configuração de banco, storage, fila e autenticação nos demais módulos de `src/app/` (SPEC-0012). |
| Backend de aplicação — autenticação | `src/app/auth.py` | Token estático de demonstração; resolve tenant/projeto/papel a partir do cabeçalho `Authorization` (DEC-002). |
| Backend de aplicação — persistência | `src/app/db.py`, `src/app/models.py`, `src/app/repo.py` | SQLAlchemy sobre PostgreSQL; tabelas `bases`/`executions`/`queries` e leituras isoladas por tenant/projeto. |
| Backend de aplicação — storage | `src/app/storage.py` | Salvar/apagar/materializar arquivos Markdown enviados, em Cloudflare R2 ou disco local. |
| Backend de aplicação — tarefa assíncrona | `src/app/tasks.py` | Tarefa Procrastinate que chama a fachada do pipeline sem bloquear a requisição HTTP; impede execução concorrente por base. |
| Backend de aplicação — endpoints | `src/app/routers/bases.py`, `executions.py`, `queries.py` | Upload/base preparada/exclusão, iniciar/consultar/repetir execução e consulta de validação sobre `service.query_base`. |
