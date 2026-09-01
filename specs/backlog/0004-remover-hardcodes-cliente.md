# Backlog: Remover hardcodes de cliente e tornar ferramentas configuráveis

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0004 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Configuração operacional reutilizável |
| Tipo | Melhoria técnica |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-08-31 |
| Spec promovida | Nenhuma |

## Ideia original

Eliminar referências fixas à C6 e à Vivo dos CLIs, demos e verificadores, usando configuração e exemplos neutros.

## Problema percebido

Scripts operacionais e demonstrações contêm branding, conteúdo e nomes de collection específicos, criando risco de uso no destino errado e acoplamento ao caso atual.

## Pessoa afetada ou beneficiada

Operadores que reutilizam o pipeline para diferentes clientes e bases.

## Resultado ou valor esperado

Toda ferramenta operacional funciona por configuração explícita e os exemplos não confundem dados de demonstração com defaults do produto.

## Contexto

Item P1 do milestone M0, identificado em chat.py, demo_rag.py e scripts/check_qdrant_connection.py.

## Referências relacionadas

- `chat.py` e `demo_rag.py`: branding e conteúdo de cliente no fluxo demonstrativo.
- `scripts/check_qdrant_connection.py`: collection específica no verificador.
- `config.yaml` e `src/config.py`: mecanismo de configuração existente.
- Linear `LEAD-87`: tracking do item no milestone M0.

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
- Auditoria e observabilidade: a avaliar.

## Dependências

- Nenhuma registrada.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: a esclarecer.
- Fora: a esclarecer.

## Dúvidas, decisões e riscos

- Nenhum registrado.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
