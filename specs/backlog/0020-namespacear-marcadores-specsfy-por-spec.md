# Backlog: Namespacear marcadores SPECSFY por especificação

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0020 |
| Status | Promoted |
| Produto | Specsfy — governança de especificações e evidências |
| Épico | Confiabilidade dos gates de qualidade |
| Funcionalidade | Rastreabilidade entre specs e testes |
| Tipo | Técnico (correção de isolamento e compatibilidade) |
| Prioridade | Alta |
| Milestones | |
| Criado em | 2026-09-15 |
| Spec promovida | `specs/draft/0016-namespacear-marcadores-specsfy-por-spec/spec.md` |

## Ideia original

Os marcadores SPECSFY nos testes não dizem a qual spec pertencem; IDs repetidos fazem check_traceability misturar cobertura e reprovar gates com marcadores órfãos.

## Problema percebido

O auditor de rastreabilidade trata IDs locais como globais, mistura cobertura entre specs e impede o enforcement confiável do repositório.

## Pessoa afetada ou beneficiada

Pessoas que validam Definition, Plan e Delivery Gates e dependem da rastreabilidade automatizada.

## Resultado ou valor esperado

Cada marcador é atribuído inequivocamente à sua spec, e o auditor conta ou rejeita apenas evidências do escopo correto.

## Contexto

Correção independente do framework Specsfy, já capturada em specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md e agora bloqueando a SPEC-0015.

## Referências relacionadas

- `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md` — captura de origem preservada.
- `specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md` — spec bloqueada pelo cruzamento indevido de IDs.
- `specs/completed/0006-gate-qualidade-chunks-metadados/spec.md` — mitigação histórica por arquivo de teste próprio.
- `specs/completed/0007-ruff-e-esteira-de-integracao-continua/spec.md` — evidência histórica de marcadores órfãos pertencentes a outras specs.
- `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` — implementação atual que indexa IDs sem namespace.
- `.agents/skills/specsfy-04-validate/scripts/verify_repo.mjs` — consumidor que executa a rastreabilidade de todas as specs concluídas.

## Comportamento esperado

- O formato novo é `SPECSFY: SPEC-NNNN <IDs locais>`, por exemplo
  `SPECSFY: SPEC-0015 US-001 FR-001 AC-001`.
- Ao validar `SPEC-NNNN`, se existir ao menos um marcador com esse namespace,
  o auditor entra em modo namespaced e considera somente os marcadores dessa
  spec. Marcadores de outras specs e marcadores legados sem namespace não
  contam como cobertura nem como órfãos.
- Quando não houver marcador do namespace alvo, o auditor mantém o modo
  legado: os IDs sem namespace continuam contando como cobertura. IDs
  estranhos nesse modo são reportados como aviso de ambiguidade, mas não
  reprovam o gate, porque não é possível atribuí-los com segurança.
- Dentro do namespace alvo, IDs inexistentes na spec continuam sendo erro e
  reprovam o gate.
- A saída humana e o JSON informam o modo usado (`namespaced` ou `legacy`) e
  preservam os campos existentes para consumidores atuais.

## Regras de negócio

- `SPEC-NNNN` é obtido do campo `ID` da tabela de metadados de `spec.md`, não
  do nome do diretório.
- O namespace deve aparecer logo após `SPECSFY:`; tokens de requisito mantêm
  o formato atual (`US`, `FR`, `NFR`, `AC`).
- Um arquivo pode conter evidências de várias specs sem que uma contamine a
  outra.
- O modo legado existe apenas para compatibilidade de leitura; specs novas ou
  migradas devem usar namespace explícito.
- A mudança não deve alterar a avaliação de tarefas, evidências ou aceites
  fora da seleção dos marcadores de teste.

## Critérios de aceitação

- Dadas duas specs que reutilizam `US-001` e `AC-001`, quando o auditor valida
  uma delas com marcadores namespaced, então somente os casos prefixados com o
  ID dessa spec contam e marcadores da outra não aparecem como órfãos.
- Dada uma spec ainda não migrada, quando não existe marcador com seu
  namespace, então os marcadores legados continuam cobrindo seus IDs e
  marcadores ambíguos de outras specs não reprovam o gate.
- Dado um marcador namespaced para a spec alvo contendo um ID que ela não
  define, quando a verificação roda, então o ID é reportado como órfão e o
  comando termina com falha.
- Dada a SPEC-0015 migrada para o formato namespaced, quando sua
  rastreabilidade é verificada na raiz do repositório, então IDs repetidos das
  specs históricas não contam como cobertura nem como órfãos da SPEC-0015.

## Qualidades e operação

- Segurança: não executa conteúdo lido e não amplia acesso ao filesystem.
- Privacidade: não aplicável; processa apenas arquivos locais de spec e testes.
- Desempenho e volume: uma única varredura da raiz, sem leitura adicional por
  spec além da já realizada; preservar ordem de grandeza atual.
- Auditoria e observabilidade: saída humana e JSON devem declarar o namespace
  alvo, o modo selecionado e os marcadores órfãos aplicáveis.

## Dependências

- Deve ser entregue antes do Plan/Delivery Gate da SPEC-0015.
- `verify_repo.mjs` depende da compatibilidade dos argumentos e do código de
  saída de `check_traceability.mjs`.

## Situações de erro

- Spec sem campo `ID` válido → erro de uso com código de saída não zero.
- Marcador do namespace alvo com ID não definido → gap de rastreabilidade.
- Namespace estrangeiro → ignorado para cobertura e órfãos da spec alvo.
- Marcador legado durante modo namespaced → ignorado, evitando falsa
  cobertura durante a migração gradual.

## Escopo

- Dentro: parser e relatório de `check_traceability.mjs`; testes automatizados
  do modo namespaced, fallback legado e órfão local; migração dos marcadores da
  SPEC-0015 e atualização de sua documentação normativa.
- Fora: migração em massa das specs concluídas; renumeração de `US`, `FR`,
  `NFR` ou `AC`; mudança nos formatos Gherkin; mudança de interface, banco,
  API ou código de produção do rag-pipeline.

## Dúvidas, decisões e riscos

- Decisão confirmada pelo usuário em 2026-09-15: evolução compatível local,
  com namespace explícito e migração gradual.
- Decisão: o modo namespaced é ativado pela presença de evidência do namespace
  alvo; isso evita que uma adoção parcial misture evidências legadas.
- Decisão: órfãos legados deixam de reprovar o gate e são apenas avisos, pois
  sua spec de origem é indeterminável; órfãos do namespace alvo permanecem
  bloqueantes.
- Risco: consumidores podem analisar texto da saída. Mitigação: preservar as
  linhas existentes e adicionar apenas a identificação do modo/namespace.
- Risco: uma spec migrada parcialmente perde cobertura dos marcadores ainda
  legados. Mitigação: migrar todos os marcadores da spec numa mesma tarefa e
  deixar o checker acusar os IDs descobertos insuficientes.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido para `specs/draft/0016-namespacear-marcadores-specsfy-por-spec/spec.md`.
