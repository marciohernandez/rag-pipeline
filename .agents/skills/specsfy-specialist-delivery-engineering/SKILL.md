---
name: specsfy-specialist-delivery-engineering
description: Projetar e revisar CI/CD, artefatos, releases, promoções, migrations, rollout, rollback e supply chain. Use para pipelines, workflows, ambientes, deploys ou estratégia de entrega; não publicar, promover ou alterar produção sem autorização explícita.
---

# Engenharia de entrega

## Fluxo

1. Mapear commit, artefato, ambientes, aprovações e owner da promoção.
2. Tornar build e testes reproduzíveis a partir de lockfiles.
3. Produzir artefato imutável uma vez e promovê-lo entre ambientes.
4. Separar credenciais, permissões e trust boundaries por job.
5. Coordenar migrations e compatibilidade entre versões.
6. Definir rollout, sinais de sucesso, pausa e rollback.
7. Registrar proveniência, versão, evidência e resultado.

## Padrões

- Usar menor privilégio, credenciais temporárias e actions/dependências fixadas.
- Não reconstruir artefato para cada ambiente.
- Impedir concorrência incompatível e deploy de commit não testado.
- Manter ambientes reproduzíveis e configuração fora do artefato.
- Exigir smoke checks e observabilidade antes de concluir rollout.
- Tratar rollback de código e de dados como problemas diferentes.
- Preservar trilha auditável sem registrar segredos.

## Validação

- Lint do pipeline, execução em branch segura e teste de falha.
- Verificação de digest, SBOM, assinatura/proveniência quando adotadas.
- Ensaio de rollout e rollback em ambiente representativo.
- Confirmação de gates, proteções e permissões do provedor.

Leia [references/standards.md](references/standards.md) para pipeline, supply
chain, migrations e estratégias de release.
