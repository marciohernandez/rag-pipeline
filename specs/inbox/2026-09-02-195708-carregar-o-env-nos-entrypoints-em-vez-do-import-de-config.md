# Inbox: Carregar o .env nos entrypoints em vez do import de config

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-02T22:57:08Z |
| Slug | carregar-o-env-nos-entrypoints-em-vez-do-import-de-config |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `79b4480ab544110643c633e5796b5fe2a8c5507952ecd73def448b6f89363765` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

src/config.py chama load_dotenv() no import do módulo. Qualquer teste ou script que importe a configuração injeta o .env inteiro no processo. Isso já quebrou o teste de credencial ausente da SPEC-0003 quando OPENAI_API_KEY foi acrescentada ao .env: o teste passava isolado e falhava na suíte completa. Blindei o teste com monkeypatch, mas a causa continua. Mover a carga para os entrypoints resolveria, mas muda comportamento de produção usado por pipeline.py, search.py e chat.py.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** load_dotenv no import de src/config.py injeta o .env no processo inteiro e cria acoplamento invisível entre testes.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Um teste que prova ausência de credencial depende de qual módulo foi importado antes dele.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem roda a suíte e quem opera os CLIs.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Testes deixam de depender do conteúdo do .env da máquina, sem perder a conveniência nos CLIs.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: o teste de credencial ausente passava isolado e falhava na suíte completa. Declaração: o teste foi blindado com monkeypatch e a causa continua. Declaração: mover a carga muda comportamento de pipeline.py, search.py e chat.py.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Risco: qualquer entrypoint esquecido perde o carregamento do .env e falha por credencial ausente.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Fatia técnica sobre carregamento de configuração e entrypoints.

## Pontos a revisar no futuro

**A revisar:** Decidir se a carga vira responsabilidade explícita de cada CLI ou de um único bootstrap compartilhado.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
