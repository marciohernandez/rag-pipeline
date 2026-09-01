---
name: specsfy-specialist-software-architecture
description: Analisar e evoluir arquitetura com boundaries, dependências, atributos de qualidade, integrações, ADRs, migração e trade-offs. Use para modularização, coupling, escalabilidade, resiliência ou decisões difíceis de reverter; não use para renomeação local sem impacto estrutural.
---

# Arquitetura de software

## Fluxo

1. Definir finalidade, restrições e cenários de atributos de qualidade.
2. Mapear estado observado, owners, dados, dependências e fluxos.
3. Identificar forças, decisões irreversíveis e riscos.
4. Comparar opções pelos mesmos critérios e custo operacional.
5. Escolher a menor estrutura que satisfaz os cenários.
6. Definir transição, compatibilidade, observabilidade e rollback.
7. Registrar decisão e verificar boundaries por testes ou análise.

## Padrões

- Dar a cada módulo responsabilidade, dados e interface claros.
- Direcionar dependências para políticas estáveis.
- Evitar serviço, fila, cache ou abstraction sem cenário consumidor.
- Separar arquitetura implementada de arquitetura desejada.
- Expressar atributos como cenários mensuráveis, não adjetivos.
- Manter decisões substituíveis locais e decisões caras explícitas.
- Evoluir por seams verificáveis em vez de reescrita total.

## Validação

- Caminhos críticos, falhas, consistência e capacidade.
- Testes de arquitetura ou dependência quando automatizáveis.
- Ensaio de migração, compatibilidade e rollback.
- Revisão dos impactos em segurança, dados e operação.

Leia [references/standards.md](references/standards.md) para views, ADRs,
boundaries, atributos e evolução.
