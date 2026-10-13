# Backlog: Runbook de deploy manual em produção

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0032 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M03 |
| Criado em | 2026-09-28 |
| Spec promovida | Nenhuma |

## Ideia original

Documentar o processo de deploy manual do sistema em produção (docker stack deploy), incluindo pré-requisitos, ordem dos passos e como verificar que o deploy funcionou.

## Problema percebido

O deploy será manual nesta fase (decisão confirmada), mas não existe hoje nenhum processo documentado de como atualizar o sistema em produção sem quebrar o Beta.

## Pessoa afetada ou beneficiada

Marcio, ao atualizar o sistema em produção sempre que uma nova versão precisar ir ao ar.

## Resultado ou valor esperado

Existe um passo a passo documentado e repetível para atualizar o ambiente de produção via Docker Swarm, reduzindo o risco de erro humano no deploy.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decorrente da decisão de Marcio em 2026-09-28 de manter o deploy manual (sem CI/CD automatizado) nesta entrega. Depende dos demais itens do marco (stack de produção, domínio/TLS, secrets) já estarem definidos.

## Referências relacionadas

- Nenhuma referência relevante encontrada.

## Comportamento esperado

Estado em 2026-10-13: o deploy é feito na VPS por `deploy/build_and_deploy.sh`, que confere os secrets, constrói as imagens no próprio nó com a etiqueta fixa `:local` e roda `docker stack deploy`; o guia de secrets existe em `deploy/SECRETS.md` (SPEC-0027).

- **Local (Pergunta 1, 2026-10-13):** o runbook fica em `deploy/RUNBOOK.md`, ao lado do `SECRETS.md`.
- **Cobertura (Pergunta 2):** atualização, primeira instalação e emergências (volta atrás e restauração do banco com o script do 0031); aponta para o script de conferência do 0029.
- **Volta atrás (Pergunta 3):** cada imagem é etiquetada com a versão (o commit) e as últimas três são guardadas; voltar é refazer o deploy com a etiqueta anterior, e `docker service rollback` entra como comando de emergência. Exige mudar `build_and_deploy.sh`, trabalho da spec deste item.
- **Migrações (Pergunta 4):** passo manual separado, antes do deploy, com backup feito antes (0031); o serviço só é atualizado depois da conferência.
- **Verificação (Pergunta 5):** a cada deploy, o script de conferência do 0029 e uma checagem rápida de login e assistente; a lista completa (login, criar Pessoa, subir uma Base e conversar com o assistente, condição de saída do M03) vale na primeira instalação e depois de mudança grande.
- **Janela (Pergunta 6):** o deploy só acontece quando não há lote em andamento (conversão, ingestão ou análise); o runbook traz a conferência como passo antes do deploy.
- **Quem faz (Pergunta 7):** só a pessoa responsável, por acesso remoto à VPS; o runbook marca o que mudaria para delegar (acessos, chaves e registro de deploys).
- **Prova (Pergunta 8, opção 3):** um teste automático confere que os comandos e arquivos citados no runbook existem (scripts, stack, secrets), e a pessoa responsável executa o runbook inteiro uma vez na VPS antes de o item ser dado como entregue.

## Regras de negócio

- Nenhum segredo, chave ou nome de domínio é escrito no runbook.
- Antes de qualquer migração ou atualização do serviço de dados, existe um backup recente.
- Nenhum comando destrutivo de banco entra no runbook como passo de rotina.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md`, `0029-dominio-https-e-reverse-proxy-para-o-beta.md`, `0030-gestao-de-secrets-de-producao-via-docker-swarm.md` — bloqueantes. O runbook documenta o processo depois que stack, domínio/TLS e secrets já existirem.

## Situações de erro

- Deploy falha no meio ou a verificação reprova: o runbook manda voltar à etiqueta anterior (ou `docker service rollback`) e, se o banco foi afetado, restaurar o último backup.
- Migração falha: o serviço não é atualizado; o runbook indica como avaliar e, se preciso, restaurar o backup feito antes.
- Lote em andamento: o deploy espera terminar.

## Escopo

- Dentro: `deploy/RUNBOOK.md` (atualização, primeira instalação e emergências), mudança do `build_and_deploy.sh` para etiquetar imagens por versão e guardar as últimas três, teste automático dos comandos e arquivos citados e a execução única do runbook pela pessoa responsável.
- Fora: deploy automático (CI/CD); delegação a outras pessoas (apenas marcada); teste automático periódico de restauração; qualquer mudança nos itens 0029 e 0031 além de ser apontado por eles.

## Dúvidas, decisões e riscos

- Decisões das Perguntas 1 a 8 de 2026-10-13, registradas em "Comportamento esperado". Área de perguntas encerrada no limite de oito.
- Em aberto: como o runbook confere "sem lote em andamento" (consulta à fila ou às telas); como guardar apenas as últimas três etiquetas; formato do registro de deploys quando houver delegação.
- Sugestão não adotada: avisar a equipe antes do deploy.
- Risco: a dependência dos itens 0029 e 0031 (o runbook cita o script de conferência e a restauração); o item só fica pronto depois deles.
- Risco: runbook desatualizado; mitigado pelo teste automático dos nomes citados.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
