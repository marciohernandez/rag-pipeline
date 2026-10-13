# Backlog: Domínio, HTTPS e reverse proxy para o Beta

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0029 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M03 |
| Criado em | 2026-09-28 |
| Spec promovida | specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md |

## Ideia original

Apontar um domínio próprio para o sistema em produção e servir a aplicação com HTTPS válido desde o início do Beta, via reverse proxy (ex.: Traefik ou Caddy) na frente dos serviços do Docker Swarm.

## Problema percebido

O sistema hoje só é acessível localmente; não há domínio, certificado nem reverse proxy configurados para expor a aplicação de forma segura.

## Pessoa afetada ou beneficiada

Marcio e a equipe de consultoria, ao acessar o sistema em produção durante o Beta.

## Resultado ou valor esperado

A aplicação é acessível por um domínio próprio com HTTPS válido, sem aviso de certificado inválido nem acesso só por IP/porta.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decidido por Marcio em 2026-09-28: domínio próprio com HTTPS desde o início (não IP/porta). Depende do stack de produção (item de dockerização) já estar de pé.

## Referências relacionadas

- Nenhuma referência relevante encontrada.

## Comportamento esperado

Atualização de 2026-10-13: a VPS já tem um Traefik compartilhado na rede `network_swarm_public`, com HTTPS automático por labels, e o stack de produção (SPEC-0022) já se conecta a essa rede sem criar proxy próprio. Este item acrescenta só as labels de domínio, redirecionamento, HSTS e limite de tentativas ao frontend, mais o teste e o script de conferência.

- **Domínio (Perguntas 1 e 2, 2026-10-13):** um subdomínio de um domínio que a pessoa já tem; o endereço entra como variável de ambiente no deploy, e o repositório e o stack guardam só a regra, sem o nome.
- **Exposição (Pergunta 3):** só o frontend é exposto pelo domínio; backend, worker, Postgres e Qdrant ficam na rede interna, e `/api/*` passa pelo frontend.
- **HTTPS (Pergunta 4):** HTTP redireciona para HTTPS e o HSTS é ativado com validade curta no começo (por exemplo, um dia), subindo depois que a configuração estiver estável.
- **Resolvedor e ponto de entrada (Pergunta 6):** nomes do resolvedor de certificado e do ponto de entrada HTTPS vêm de variáveis de ambiente, com padrões comuns (`letsencrypt` e `websecure`), ajustáveis aos nomes reais da VPS.
- **Login público com limite (Pergunta 7):** qualquer pessoa na internet pode abrir a tela de login, com login por pessoa e limite de tentativas por endereço, aplicado por um middleware do Traefik.
- **Verificação (Pergunta 5):** um teste automático confere no stack as labels de domínio, redirecionamento, HSTS, limite de tentativas e exposição só do frontend; um script de conferência, rodado depois do deploy, consulta o domínio, o certificado e o redirecionamento. O runbook (0032) aponta para o script.

## Regras de negócio

- Nenhum nome de domínio, credencial ou segredo é versionado.
- Nenhum reverse proxy próprio é criado por este stack.
- Só o frontend recebe labels de exposição.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — bloqueante. O reverse proxy e o HTTPS precisam do stack de produção já rodando no Swarm.

## Situações de erro

- Domínio sem DNS apontado ou certificado não emitido: o script de conferência acusa e o deploy não é desfeito; a pessoa corrige o DNS ou os nomes do resolvedor.
- Variável de domínio ausente no deploy: o deploy recusa seguir, com mensagem clara (a detalhar na spec).

## Escopo

- Dentro: labels do Traefik no frontend (domínio, redirecionamento, HSTS, limite de tentativas), variáveis de ambiente correspondentes, teste automático das labels e script de conferência pós-deploy.
- Fora (confirmado na Pergunta 8): instalar ou configurar o Traefik da VPS; registrar o domínio e criar o registro DNS; mais de um domínio ou o endereço com `www`; firewall de aplicação, CDN e proteção contra ataques de grande volume; página de manutenção; restrição por IP ou VPN.

## Dúvidas, decisões e riscos

- Decisões das Perguntas 1 a 8 de 2026-10-13, registradas em "Comportamento esperado". Área de perguntas encerrada no limite de oito.
- Em aberto: valor do limite de tentativas (quantas por minuto) e da validade final do HSTS; nomes reais do resolvedor e do ponto de entrada na VPS (mostrar as labels de um serviço vizinho que já funciona).
- Risco: HSTS errado pode prender o navegador em HTTPS com configuração quebrada; mitigado pela validade curta no começo.
- Verificação real do certificado só na VPS (mesmo limite da SPEC-0022).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
