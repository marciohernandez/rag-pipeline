# Backlog: Reconciliar specs concluídas com o enforcement atual

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0021 |
| Status | Promoted |
| Produto | Specsfy — governança e enforcement |
| Épico | Compatibilidade evolutiva dos gates |
| Funcionalidade | Verificação de specs concluídas |
| Tipo | Técnico (correção de compatibilidade histórica) |
| Prioridade | Alta |
| Milestones | |
| Criado em | 2026-09-15 |
| Spec promovida | `specs/defined/0017-reconciliar-specs-concluidas-com-o-enforcement-atual/spec.md` |

## Ideia original

O enforcement global deve validar specs concluídas sem fabricar evidência retroativa e sem reprovar por caminhos movidos ou ausência legítima de research externo.

## Problema percebido

Validadores atuais aplicam contratos novos às specs históricas: evidence rejeita arquivos movidos para src/pipeline, research exige artefato mesmo quando não há claim formal e full-chain exige cobertura de evidence por ID que não existia no modelo legado.

## Pessoa afetada ou beneficiada

Pessoas mantenedoras e automações que usam verify_repo como gate global.

## Resultado ou valor esperado

verify_repo verde com compatibilidade auditável: evidência histórica provada pelo Git, research opcional quando não aplicável e cadeia estrita preservada para specs namespaced.

## Contexto

Derivado de specs/inbox/2026-09-15-163521-reconciliar-specs-concluidas-com-o-enforcement-atual.md e do inventário executado em 2026-09-15 após a SPEC-0016.

## Referências relacionadas

- `specs/inbox/2026-09-15-163521-reconciliar-specs-concluidas-com-o-enforcement-atual.md` — captura de origem.
- `specs/in-progress/0016-namespacear-marcadores-specsfy-por-spec/spec.md` — spec bloqueada pelo enforcement histórico.
- `.agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs` — rejeita arquivos históricos movidos.
- `.agents/skills/specsfy-03-specify/scripts/load_research.mjs` — exige artefato mesmo quando research não se aplica e não acompanha mudança de estado.
- `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` — exige evidence por ID em `--full-chain` para specs legadas.
- `.agents/skills/specsfy-04-validate/scripts/verify_repo.mjs` — orquestrador que expõe as incompatibilidades.

## Comportamento esperado

- Em uma spec `Complete`, arquivo citado por evidence é válido quando existe no
  checkout atual ou quando `git log` comprova que esse caminho existiu na
  ancestralidade da branch atual; o resultado deve distinguir evidência atual
  de histórica.
- Em spec ativa, o arquivo citado continua obrigado a existir no checkout
  atual; história Git não mascara entrega incompleta.
- Ausência de artefato em `research/` é válida quando não há claim formal
  `ResearchClaim` nem caminho indexado.
- Um caminho indexado sob outro estado da mesma spec resolve para o diretório
  atual da spec, preservando o sufixo interno de `research/`.
- `--full-chain` em modo legado exige teste e tarefa, enquanto a prova material
  permanece a cargo de `verify_evidence`; em modo namespaced continua exigindo
  teste, tarefa e evidence por ID.

## Regras de negócio

- Compatibilidade só se aplica a `Status: Complete`; specs ativas permanecem
  estritas.
- Um caminho histórico só é aceito se estiver dentro da raiz e aparecer no
  histórico da branch atual; não usar `--all`, symlink ou caminho externo.
- A ausência legítima de research produz lista vazia e sucesso, não cria
  artefato fictício.
- Claims formais, caminhos indexados inseguros, budgets e claims críticos
  continuam sujeitos ao contrato estrito.
- O modo namespaced é o ponto de corte explícito para a cadeia por ID.

## Critérios de aceitação

- Dada uma spec concluída que cita arquivo posteriormente movido, quando o
  caminho original existe no histórico Git da branch, então evidence passa e
  informa que o arquivo é histórico.
- Dada uma spec ativa com o mesmo caminho ausente, então evidence reprova.
- Dada uma spec sem claim formal nem artefato indexado, então research passa
  com zero artefatos; dado um caminho antigo de estado da mesma spec, ele é
  resolvido para o pacote atual.
- Dada uma spec legada completa, então `--full-chain` não reprova apenas por
  evidence ausente por ID; dada uma spec namespaced equivalente, essa ausência
  continua bloqueante.
- Dado o repositório atual, `verify_repo.mjs` termina com sucesso sem editar as
  evidências históricas das specs concluídas.

## Qualidades e operação

- Segurança: paths continuam confinados à raiz; Git recebe argumentos
  estruturados sem shell; symlinks e traversal permanecem recusados.
- Privacidade: não aplicável; somente metadados e arquivos versionados locais.
- Desempenho e volume: consulta Git ocorre apenas para arquivo ausente de spec
  concluída; repositório atual deve terminar dentro do timeout de 300 s.
- Auditoria e observabilidade: JSON identifica arquivos aceitos pelo histórico
  e o relatório global mantém cada check individual.

## Dependências

- Git disponível e checkout com histórico local suficiente.
- Deve concluir antes de fechar T006/Delivery Gate da SPEC-0016.

## Situações de erro

- Arquivo ausente sem prova no Git → evidence falha.
- Git indisponível ou diretório sem repositório → não aplicar grandfathering.
- Claim formal sem evidence local → research falha.
- Caminho indexado de outra spec → research falha como inseguro.
- Spec namespaced sem evidence por ID em `--full-chain` → cadeia quebrada.

## Escopo

- Dentro: testes e mudanças nos três validadores; enforcement real do
  repositório; retomada da SPEC-0016 após o gate global ficar verde.
- Fora: editar evidence inline das specs concluídas; fabricar commits,
  atestações ou research; relaxar specs ativas; alterar aplicação, banco ou UI.

## Dúvidas, decisões e riscos

- Decisão: usar a ancestralidade Git como prova imutável de arquivo histórico,
  em vez de reescrever evidência inline.
- Decisão: `research/` é opcional quando não há claim formal nem artefato
  indexado; ausência não equivale a erro.
- Decisão: namespace explícito ativa a cadeia estrita por ID; legado delega a
  materialidade ao verificador de evidence.
- Risco: repositório raso pode não conter o caminho antigo. Nesse caso o gate
  permanece vermelho, sem fallback permissivo.
- Risco: arquivo existiu antes da tarefa. O contrato schema 1 não possui commit
  binding; a aceitação histórica reconhece essa limitação e não substitui
  atestação schema 2 para novas entregas.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido para SPEC-0017; seguir o planejamento normativo na spec.
