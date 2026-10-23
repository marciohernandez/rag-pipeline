# Inbox: Owner e copilot com acesso a tudo, sem separação por tenant

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T12:39:41Z |
| Slug | owner-e-copilot-com-acesso-a-tudo-sem-separacao-por-tenant |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `a7f223a6a91b57b3862ce5e62b4f4bd2504360024a7c6a21ec010a551b8166ac` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

o owner não preciso ter tenant e projeto, ele ve tudo, não deve estar preciso a isso não acha? ... como owner eu preciso de acesso a tudo assim como meu copilot. não posso estar separado por tennant

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A pessoa owner (e o copilot dela) deve enxergar e gerenciar todos os dados do sistema, sem ficar presa a um tenant e projeto.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Hoje o owner é criado com tenant e projeto obrigatórios e só vê o que está dentro deles; toda consulta filtra por esse par (SPEC-0020). Para quem administra vários clientes, isso separa o que deveria ser visto junto.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** O owner do sistema (a consultoria) e o copilot que atua com o acesso dele.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Um owner global que acessa todos os Workspaces e dados de qualquer tenant, sem trocar de contexto, e um copilot com o mesmo alcance.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: o owner não deveria precisar de tenant e projeto; precisa de acesso a tudo, assim como o copilot; não pode ficar separado por tenant. Inferência: exige um papel ou escopo global distinto do owner por tenant e mudança nas consultas filtradas por tenant e projeto. Contexto observado: create_owner exige --nome, --tenant e --projeto; src/app/create_owner.py.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Provável necessidade de guardar que um owner tem escopo global (sem tenant e projeto fixos) e quais tenants ele enxerga; a confirmar em conversa futura.

### Riscos e dependências

**Análise preliminar:** Mudança de segurança: afrouxa o isolamento entre tenants, hoje decisão da SPEC-0020. Risco de vazamento entre clientes se o escopo global for mal protegido. O copilot (SPEC-0031) herdaria o alcance, ampliando o que o assistente consegue ler. Dependências: SPEC-0020 (autenticação), SPEC-0031 (copilot), consultas em src/app/repo.py.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possível spec para papel de owner global; possível ajuste do create_owner para dispensar tenant e projeto. Nada promovido.

## Pontos a revisar no futuro

**A revisar:** Owner global vê todos os tenants ou só administra? O copilot herda o alcance total? Haverá mais de um owner global? Como auditar o acesso entre tenants? Como ficam pessoas e conexões, hoje por tenant? Tratar depois do M04.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
