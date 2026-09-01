# Backlog: Bloquear recriação destrutiva e garantir sincronização segura

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0001 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Segurança da sincronização vetorial |
| Tipo | Técnico |
| Prioridade | P0 — urgente |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | `specs/defined/0001-bloquear-recriacao-destrutiva/spec.md` |

## Ideia original

Remover ou bloquear os caminhos de --recreate e as orientações que promovem operações remotas destrutivas, preservando a sincronização incremental segura e documentando recuperação sem perda ampla de dados.

## Problema percebido

O pipeline e sua documentação ainda expõem --recreate, capaz de apagar collection ou namespace remoto e incompatível com a política de segurança do projeto.

## Pessoa afetada ou beneficiada

Operadores e mantenedores do rag-ingestion-pipeline, além da futura integração com o rag-pipeline.

## Resultado ou valor esperado

Nenhum fluxo normal consegue recriar ou apagar amplamente a base remota; sincronização e recuperação ficam seguras, previsíveis e testáveis.

## Contexto

Item P0 do milestone M0, identificado na auditoria do código, CLI e documentação existentes.

## Referências relacionadas

- `PROJECT.md`: limite explícito para operações remotas destrutivas.
- `.specsfy/RULES.md`: segurança, configuração centralizada e qualidade antes da integração.
- `.specsfy/DATABASE.md`: comportamento vigente do modo espelho no Qdrant.
- `pipeline.py`, `upsert_from_chunks.py` e `src/embedder.py`: caminhos executáveis de recriação e sincronização.
- `README.md`, `GUIA_DE_USO.md` e `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`: comandos e orientações históricas sobre `--recreate`.
- `PLANO_CHUNKS_RESUMO_QDRANT.md`: precedente para fail-fast, identidades estáveis e sincronização após upsert bem-sucedido.
- Linear `LEAD-88`: tracking do item no milestone M0.

## Comportamento esperado

1. O fluxo operacional padrão aceita somente processamento local, upsert idempotente e sincronização incremental com escopo explícito.
2. `--recreate` e equivalentes não podem iniciar exclusão de collection, índice ou namespace remoto.
3. Uma tentativa de usar opção destrutiva falha antes de criar cliente remoto, gerar embeddings ou alterar dados.
4. O modo espelho preserva pontos fora do `project_id` da execução e remove obsoletos do mesmo escopo somente após o upsert completo e bem-sucedido.
5. Falha de carregamento, chunking, embedding ou upsert encerra a execução sem iniciar a limpeza de pontos obsoletos.
6. A recuperação operacional usa nova execução idempotente, manifesto e diagnóstico; não orienta apagar a base inteira.
7. CLI, código, testes e documentação descrevem o mesmo contrato seguro.

## Regras de negócio

- A pasta Markdown validada e o manifesto da execução definem o conjunto esperado apenas dentro do `project_id` configurado.
- A ausência, vazio ou inconsistência do escopo impede qualquer remoção remota.
- Upsert deve preceder limpeza de obsoletos; a limpeza não ocorre quando o upsert falha ou fica parcial.
- IDs pertencentes a outro projeto, tenant, collection ou namespace não podem ser removidos pela execução atual.
- Compatibilidade com uma flag antiga pode produzir erro de migração claro, mas nunca executar a ação destrutiva.
- Credenciais, URLs e nomes de collection ou namespace não aparecem em logs além do que a configuração segura já permite.

## Critérios de aceitação

```gherkin
Scenario: Bloqueio de uma opção de recriação
  Given uma configuração válida para um banco vetorial remoto
  When o operador tenta executar o pipeline com --recreate
  Then a execução termina com mensagem segura antes de qualquer mutação remota

Scenario: Sincronização idempotente sem alterações
  Given uma execução anterior concluída para o mesmo project_id
  When os mesmos documentos são processados novamente
  Then nenhum ponto duplicado é criado e nenhum ponto válido é removido

Scenario: Falha antes da limpeza
  Given que existem pontos válidos e obsoletos no escopo do projeto
  When o upsert dos pontos atuais falha ou fica incompleto
  Then a limpeza dos pontos obsoletos não é iniciada

Scenario: Isolamento entre projetos
  Given pontos de dois project_id na mesma collection
  When a sincronização em modo espelho conclui para um deles
  Then somente pontos obsoletos daquele project_id podem ser removidos

Scenario: Documentação operacional segura
  Given os guias e exemplos publicados no repositório
  When o operador procura como atualizar ou recuperar uma base
  Then encontra somente fluxos idempotentes e nenhuma orientação para recriar ou limpar amplamente o destino remoto
```

## Qualidades e operação

- Segurança: falhar fechado antes de qualquer mutação quando escopo, manifesto ou configuração forem inválidos; nenhuma opção destrutiva no fluxo normal.
- Privacidade: manter isolamento lógico por `project_id`; a futura inclusão de `tenant_id` pertence ao BACKLOG-0002.
- Desempenho e volume: preservar upsert em lote e comparar IDs sem exigir recriação integral da collection.
- Auditoria e observabilidade: registrar modo, escopo lógico e contagens previstas, inseridas, mantidas e removidas, sem segredos.

## Dependências

- Preserva as identidades determinísticas e o manifesto já implementados.
- BACKLOG-0002 deverá ampliar o contrato de escopo para integração multi-tenant sem reabrir a proteção básica deste item.
- BACKLOG-0003 deverá manter estas garantias ao separar os adapters de providers.

## Situações de erro

- Flag destrutiva antiga: rejeitar com orientação de migração para sincronização segura.
- `project_id` ausente ou vazio: bloquear qualquer limpeza.
- Manifesto incompleto ou divergente: encerrar sem remover pontos.
- Falha parcial de embedding ou upsert: encerrar sem etapa de limpeza.
- Destino remoto inacessível: relatar falha sem tentar recuperação destrutiva.

## Escopo

- Dentro: CLI e chamadas internas de recriação; Qdrant, ChromaDB e Pinecone expostos pelo componente; ordem segura de sincronização; testes; README e guias operacionais.
- Fora: migração de dados entre providers; backup administrado pelo fornecedor; autenticação; interface web; contrato multi-tenant completo; modularização arquitetural dos providers.

## Dúvidas, decisões e riscos

- Decisão confirmada por contexto: operações destrutivas ficam fora do fluxo normal e não serão oferecidas como caminho de recuperação.
- Inferência a validar na spec: manter a flag antiga apenas como erro explícito pode oferecer migração mais clara que removê-la silenciosamente.
- Risco: ChromaDB e Pinecone não têm paridade de sincronização segura comprovada; a spec deve exigir bloqueio conservador quando a garantia não puder ser sustentada.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido em 2026-08-31 para `specs/defined/0001-bloquear-recriacao-destrutiva/spec.md`.
A fonte normativa passa a ser a spec; este backlog preserva apenas a proveniência
e não governa mais o comportamento.
