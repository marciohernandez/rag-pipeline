# Backlog: Compatibilizar o contrato Markdown do projeto-mãe

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0002 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Contrato de integração Markdown |
| Tipo | Técnico |
| Prioridade | P0 — urgente |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | specs/draft/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md |

## Ideia original

Preservar metadados recebidos do rag-pipeline, incluindo document_id, tenant_id, type, version e status, e tratar documentos de perguntas e respostas separados por ---.

## Problema percebido

A auditoria de `src/identity.py`, `src/loader.py` e `src/chunker.py` encontrou:

- `document_id` e `project_id` recebidos no frontmatter são sobrescritos
  incondicionalmente pela identidade determinística local
  (`src/identity.py:26-27`).
- `tenant_id` não participa da identidade nem do escopo lógico da
  sincronização; `SyncSafetyPolicy.assert_valid_scope` valida somente
  `project_id` e `chunk_id` (`src/safety.py:66-98`). Em modo espelho, dois
  tenants no mesmo `project_id` fariam a remoção de obsoletos apagar pontos de
  um tenant ao sincronizar o outro.
- `type`, `version` e `status` não têm efeito algum no processamento hoje.
- O formato Q&A do projeto-mãe (blocos separados por `---`) colide com o
  delimitador de frontmatter YAML: um documento Q&A que começa com `---` tem o
  primeiro bloco engolido como se fosse YAML e descartado do `page_content`
  (`src/loader.py:28-29`). Nenhum splitter reconhece o separador; pares
  pergunta/resposta são cortados por tamanho, não por conteúdo.
- Os sete documentos hoje em `documentos/vivo_gold_banda_larga_pf/` não têm
  frontmatter algum — o contrato nunca foi exercitado na prática.

## Pessoa afetada ou beneficiada

Equipe que integrará o rag-ingestion-pipeline ao rag-pipeline e operadores de bases multi-tenant.

## Resultado ou valor esperado

Documentos validados pelo projeto-mãe entram no componente sem perda semântica de identidade, escopo ou estrutura Q&A.

## Contexto

Item P0 do milestone M0, limitado à preparação de compatibilidade futura sem
implementar a V1 do projeto-mãe. O contrato do `rag-pipeline` ainda não está
congelado (projeto-mãe em estágio inicial); os cinco campos são previstos,
mas seus valores permitidos (especialmente `type` e `status`) ainda não são
conhecidos. O componente deve tolerar essa evolução sem quebrar.

## Referências relacionadas

- `PROJECT.md`: fronteira entre o componente e o projeto-mãe.
- `.specsfy/DATABASE.md`: identidades e ausência atual de tenant persistente.
- `src/identity.py`, `src/loader.py`, `src/chunker.py` e `src/safety.py`:
  contrato e guardas implementados hoje.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md`: guarda de
  escopo entregue, que valida somente `project_id` e `chunk_id`.
- `specs/backlog/0005-gate-qualidade-chunks-metadados.md`: valida a qualidade
  do chunk de saída; este item define o contrato de entrada.
- `specs/backlog/0004-remover-hardcodes-cliente.md`: `project_id` hoje vem de
  `config.yaml` fixo, não do frontmatter.
- Fontes fornecidas do projeto-mãe: `briefing.md`, `tech_stack.md` e
  constituição 1.2.1.
- Linear `LEAD-86`: tracking do item no milestone M0.

## Comportamento esperado

1. **Identidade do documento.** Quando o frontmatter declarar `document_id`,
   esse valor prevalece como identidade do documento e participa da geração
   de `chunk_id` de todos os seus chunks. Na ausência dele, o pipeline mantém
   a geração determinística atual (`stable_uuid` a partir de `project_id` e
   caminho). Como `document_id` compõe a `base_key` do `chunk_id`
   (`src/identity.py:53-56`), a primeira execução sobre uma base já indexada
   com essa mudança regenera todos os `chunk_id` e exige reindexação completa
   — segura em modo espelho porque o SPEC-0001 garante upsert confirmado
   antes de remover os obsoletos, mas cara e deve ser prevista.
2. **Escopo multi-tenant.** `tenant_id` é opcional. Quando ausente em todo o
   lote, o comportamento atual não muda. Quando presente em ao menos um
   documento do lote, todos os documentos do lote precisam declará-lo com o
   mesmo valor; o escopo lógico da sincronização passa a ser
   `tenant_id + project_id`, e a remoção de obsoletos em modo espelho é
   filtrada pelos dois. Lote com `tenant_id` divergente entre documentos, ou
   com mistura de documentos com e sem `tenant_id`, é recusado antes de tocar
   o destino (extensão de `SyncSafetyPolicy.assert_valid_scope`).
3. **Bloqueio por status.** Documento com `status` ausente ou não reconhecido
   é tratado como aprovado (fail-open, compatível com a base atual sem
   frontmatter). Uma lista de valores de `status` que bloqueiam a indexação
   fica configurável em `config.yaml`, vazia por padrão.
4. **Versão.** `version` é gravado no payload do chunk como metadado de
   auditoria e consulta, sem efeito na identidade. Reindexação de um
   `document_id` já indexado com `version` diferente segue o fluxo idempotente
   existente, dirigido por `source_hash`/`chunk_hash`.
5. **Tipo.** `type` é gravado no payload do chunk como metadado de auditoria e
   filtro de consulta, sem efeito no chunking, identidade ou bloqueio de
   indexação.
6. **Formato Q&A.** Um documento declara o splitter Q&A explicitamente no
   frontmatter (`splitter: qa`, reaproveitando o mecanismo já existente em
   `src/chunker.py:23`). O corpo desse documento usa `++++` como separador de
   blocos pergunta/resposta — não `---`, para eliminar a colisão com o
   delimitador de frontmatter YAML. Cada bloco entre `++++` vira exatamente um
   chunk, sempre, independentemente do tamanho; o splitter por
   headers/caracteres não se aplica a esse tipo de documento. Documento sem
   `splitter: qa` no frontmatter continua no fluxo padrão mesmo que o corpo
   contenha `++++` por coincidência.

## Regras de negócio

- `document_id` do frontmatter tem precedência sobre a identidade
  determinística local; ausência de `document_id` preserva o comportamento
  atual.
- Lote de sincronização com `tenant_id` divergente, ou com mistura de
  documentos com e sem `tenant_id`, é recusado inteiro antes de qualquer
  chamada remota.
- Remoção de obsoletos em modo espelho nunca cruza `tenant_id`: o filtro de
  limpeza usa `tenant_id + project_id` quando `tenant_id` estiver em uso no
  lote.
- Documento com `status` na lista configurada como bloqueante não é
  indexado; a lista é vazia por padrão e não vem fixada pelo componente.
- `type` e `version` nunca alteram chunking, identidade ou decisão de
  bloqueio — são preservados apenas como metadado.
- Splitter Q&A só ativa por declaração explícita de `splitter: qa` no
  frontmatter; nunca por detecção automática de conteúdo.

## Critérios de aceitação

- Dado um documento com `document_id` no frontmatter, quando processado,
  então esse `document_id` aparece no metadata do documento e de todos os
  seus chunks, e nenhum novo UUID determinístico é gerado para o documento.
- Dado um documento sem `document_id` no frontmatter, quando processado,
  então o pipeline gera o `document_id` determinístico como faz hoje, sem
  regressão.
- Dado um lote onde todo documento declara o mesmo `tenant_id`, quando
  sincronizado em modo espelho, então a remoção de obsoletos afeta somente
  pontos do mesmo `tenant_id` e `project_id`.
- Dado um lote onde documentos declaram `tenant_id` divergentes entre si,
  quando a sincronização é chamada, então a operação é recusada com
  `InvalidSyncScopeError` antes de qualquer chamada ao destino remoto.
- Dado um lote onde parte dos documentos declara `tenant_id` e parte não,
  quando a sincronização é chamada, então a operação é recusada com
  `InvalidSyncScopeError` antes de qualquer chamada ao destino remoto.
- Dado um documento com `status` presente na lista bloqueante configurada,
  quando processado, então o documento é excluído da indexação e o motivo é
  registrado no log/manifesto.
- Dado um documento com `status` ausente, ou com valor fora da lista
  bloqueante, quando processado, então o documento é indexado normalmente.
- Dado um documento Markdown com frontmatter `splitter: qa` e corpo separado
  por `++++`, quando chunkado, então cada bloco entre `++++` vira exatamente
  um chunk, sem cortes de tamanho no meio de um par pergunta/resposta.
- Dado um documento Markdown que começa com `---` mas não declara
  `splitter: qa`, quando carregado, então o comportamento de frontmatter
  atual não muda e nenhum conteúdo é perdido por engano.
- Dado um documento com `type` e `version` no frontmatter, quando indexado,
  então ambos aparecem no payload do chunk, sem afetar chunking, identidade
  ou bloqueio de indexação.

## Qualidades e operação

- Segurança: a extensão do escopo lógico para `tenant_id + project_id`
  fecha uma via de perda de dados entre tenants ainda não coberta pelo
  SPEC-0001; sem essa extensão, um lote mal-formado poderia apagar pontos de
  outro tenant em modo espelho.
- Privacidade: nenhum dado sensível novo é introduzido; os campos tratados
  (`document_id`, `tenant_id`, `type`, `version`, `status`) são identificadores
  e rótulos operacionais.
- Desempenho e volume: a mudança de origem de `document_id` força reindexação
  completa da base afetada na primeira execução após a migração; deve ser
  comunicada como operação pontual, não recorrente.
- Auditoria e observabilidade: documento excluído por `status` bloqueante
  deve deixar rastro no log e/ou manifesto, para não parecer uma falha de
  carga.

## Dependências

- Nenhuma registrada. Não depende de código ainda não entregue de outro
  backlog do M0.

## Situações de erro

- Frontmatter com `tenant_id` divergente entre documentos do mesmo lote:
  sincronização recusada antes de qualquer chamada remota.
- Frontmatter com `splitter: qa` mas corpo sem nenhum `++++`: o documento
  inteiro vira um único chunk pelo comportamento padrão da estratégia (a
  esclarecer na especificação se isso deve gerar aviso).
- Frontmatter malformado ou com tipo inesperado para um destes campos: o
  parser YAML já existente (`src/loader.py`) trata o erro e loga; este item
  não amplia esse tratamento além dos cinco campos listados.

## Escopo

- Dentro: contrato de recepção de `document_id`, `tenant_id`, `type`,
  `version` e `status` no frontmatter; extensão da guarda de escopo lógico
  para `tenant_id`; bloqueio configurável por `status`; formato Q&A com
  separador `++++` e ativação explícita por `splitter: qa`.
- Fora: implementação de autenticação, autorização ou persistência
  multi-tenant no destino vetorial além do filtro de escopo lógico; qualquer
  comportamento do `rag-pipeline` em si; congelamento definitivo dos valores
  permitidos de `type` e `status` (permanecem abertos até o projeto-mãe
  publicar o contrato); novas estratégias de chunking do LangChain além de
  header/caracteres/Q&A — registrado como ideia futura, não escopo deste item.

## Dúvidas, decisões e riscos

- Decisão: contrato do projeto-mãe ainda não está congelado; campos previstos,
  mas sem lista fechada de valores para `type`/`status`.
- Decisão: `document_id` do frontmatter prevalece sobre a identidade local.
- Decisão: `tenant_id` opcional, estrito quando presente (tudo ou nada no
  lote), compõe o escopo lógico junto com `project_id`.
- Decisão: `status` bloqueia por lista configurável, vazia por padrão
  (fail-open).
- Decisão: `version` é metadado sem efeito na identidade.
- Decisão: `type` é metadado sem efeito no processamento.
- Decisão: separador Q&A é `++++`, não `---`, para eliminar a colisão com o
  delimitador de frontmatter.
- Decisão: splitter Q&A ativa somente por `splitter: qa` explícito no
  frontmatter, nunca por detecção automática de conteúdo.
- Risco: a primeira execução após adotar `document_id` externo força
  reindexação completa da base atual; deve ser comunicado ao operador antes
  da mudança entrar em produção.
- Ideia futura registrada, fora de escopo: abrir configuração para outras
  estratégias de chunking oferecidas pelo LangChain (Text Splitter, Markdown,
  etc.) além das três atuais. Pode virar um novo item de backlog quando
  houver necessidade concreta.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promover para `$specsfy-03-specify`.
