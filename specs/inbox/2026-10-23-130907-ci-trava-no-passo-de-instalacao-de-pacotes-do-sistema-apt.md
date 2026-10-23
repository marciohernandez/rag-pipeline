# Inbox: CI trava no passo de instalação de pacotes do sistema (apt)

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T13:09:07Z |
| Slug | ci-trava-no-passo-de-instalacao-de-pacotes-do-sistema-apt |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `d793651d7ac9fc4d07ce7c3568547f0013d0fefa6a5b8115fdbf044e66d65fd0` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

eu sempre fico com esse teste pendente, tem algo errado (CI do GitHub: job "Ruff and Pytest" fica pendente por muito tempo; ocorreu nos PRs #77 e #78)

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** O job Ruff and Pytest às vezes fica pendente por 15 a 30 minutos porque o passo que instala tesseract e libreoffice por apt-get é lento, sem limite de tempo nem nova tentativa.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Nos PRs #77 e #78, uma das duas execuções do CI (push ou pull_request) ficou pendente. No PR #78 o passo Install system packages for document conversion levou cerca de 16 minutos (12:49 a 13:05 UTC); as execuções boas levam cerca de 6 minutos no job inteiro. Os testes e o Ruff não eram a causa.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem abre PRs e espera o CI liberar o merge.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** CI previsível: o job falha rápido ou tenta de novo em vez de ficar pendente, sem exigir cancelar e reexecutar à mão.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: a pessoa relatou ficar sempre com o teste pendente. Observado: .github/workflows/ci.yml roda em push e em pull_request, o que dobra as chances de pegar um runner lento; o passo do apt não tem timeout-minutes nem retry. Contorno usado: gh run cancel e gh run rerun, que passaram em cerca de 6 minutos.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Cache ou retry de apt altera o pipeline de entrega; revisar a política de gates e de enforcement do repositório antes. Reduzir os gatilhos do CI muda o que bloqueia o merge.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possíveis ajustes no ci.yml: timeout-minutes e retry no passo do apt, cache dos pacotes, e limitar push à main. Nada promovido.

## Pontos a revisar no futuro

**A revisar:** Adicionar timeout e retry ou cache? Limitar o gatilho de push? Qual limite de tempo é aceitável para o passo?

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
