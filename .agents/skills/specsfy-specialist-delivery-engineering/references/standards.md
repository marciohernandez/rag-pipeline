# Padrões e referências de entrega

## Pipeline

- Etapas mínimas: validação, build, testes, análise, empacotamento e promoção.
- Cache acelera, mas nunca substitui lockfile nem verificação de integridade.
- Proteja contextos de PRs externos e não disponibilize secrets a código não confiável.
- Use concurrency e environments para controlar mutações.

## Release

- Rolling: exige compatibilidade mista.
- Blue/green: exige roteamento e estratégia de dados.
- Canary: exige métricas e limite automático.
- Feature flag: exige owner, expiração e comportamento seguro.

## Fontes primárias

- GitHub Actions: https://docs.github.com/actions
- OpenID Connect: https://docs.github.com/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- SLSA: https://slsa.dev/spec/
- OpenSSF Scorecard: https://securityscorecards.dev/
- OCI Distribution: https://github.com/opencontainers/distribution-spec
- OWASP CI/CD Security: https://owasp.org/www-project-top-10-ci-cd-security-risks/
