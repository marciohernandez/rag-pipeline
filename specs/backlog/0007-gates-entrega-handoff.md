# Backlog: Completar gates de entrega e handoff para o projeto-mãe

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0007 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de entrega e integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-08-31 |
| Spec promovida | Nenhuma |

## Ideia original

Consolidar Ruff, testes críticos, documentação segura e um contrato de handoff para incorporar este componente ao rag-pipeline.

## Problema percebido

A suíte atual tem nove testes, Ruff não está disponível no ambiente e a documentação ainda contém comandos destrutivos, impedindo considerar o componente pronto para integração.

## Pessoa afetada ou beneficiada

Mantenedores do componente e equipe que montará o projeto completo rag-pipeline.

## Resultado ou valor esperado

O milestone M0 encerra com evidências reproduzíveis de qualidade e instruções claras para integrar o componente sem carregar dívidas ou pressupostos ocultos.

## Contexto

Item P1 final do milestone M0, dependente dos backlogs anteriores e sem antecipar funcionalidades do MVP do projeto-mãe.

## Referências relacionadas

- `.specsfy/RULES.md`: Ruff, Pytest, branch por fase e workflow Specsfy.
- `pyproject.toml` e `tests/`: ferramentas e cobertura existentes.
- `docs/`, `README.md` e `GUIA_DE_USO.md`: documentação de operação e integração.
- BACKLOG-0001 a BACKLOG-0006: dependências funcionais e de qualidade do handoff.
- `.specsfy/RULES.md`, seção Testes: regra confirmada que exige o workflow de
  integração contínua verde para concluir o M0.
- `docs/testing.md`: registra Ruff como gate confirmado ainda não instalado no
  ambiente e atribui a lacuna a este item.
- Linear `LEAD-92`: tracking do item no milestone M0.

## Comportamento esperado

A esclarecer.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: o workflow de integração contínua verde é a
  evidência reproduzível de qualidade exigida para encerrar o M0. Seu registro
  de execução não expõe credenciais, tokens nem valores de ambiente.

## Dependências

- BACKLOG-0001 a BACKLOG-0006: o handoff só fecha depois que a segurança da
  sincronização, o contrato Markdown, a modularização dos providers, a remoção
  de hardcodes, o gate de qualidade dos chunks e a validação de recuperação
  estiverem resolvidos.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: instalar e configurar Ruff, hoje ausente do ambiente; workflow de
  integração contínua executando Ruff e a suíte Pytest a cada push de branch de
  fase, sem depender de execução manual; remoção dos comandos destrutivos
  remanescentes na documentação; contrato de handoff para o `rag-pipeline`.
- Fora: pipeline de deploy, publicação de pacote e ambientes gerenciados; APM,
  tracing distribuído e métricas em serviço externo; qualquer funcionalidade do
  MVP do projeto-mãe.

## Dúvidas, decisões e riscos

- Decisão confirmada em 2026-08-31, durante `$specsfy-setup`: o critério de
  "pronto" do M0 exige Ruff e Pytest verdes localmente e em integração contínua
  a cada push de branch de fase. Registrada em `.specsfy/RULES.md`, seção
  Testes.
- Hipótese, não decisão: o repositório usa GitHub e tem histórico de pull
  request, o que torna GitHub Actions a plataforma mais provável do workflow.
  A escolha ainda não foi confirmada pela pessoa responsável.
- Aberto: as demais lacunas marcadas como "a esclarecer" seguem pendentes; o
  refinamento completo deste item ainda não foi realizado.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
