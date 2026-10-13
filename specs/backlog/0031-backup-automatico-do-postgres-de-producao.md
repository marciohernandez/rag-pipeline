# Backlog: Backup automático do Postgres de produção

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0031 |
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

Configurar snapshot diário automático (ex.: pg_dump agendado) do Postgres de produção, com retenção definida, cobrindo Pessoas, Bases, execuções e conversas do assistente.

## Problema percebido

O Postgres de produção guardará dados reais de pessoas e conversas desde o primeiro dia do Beta, sem nenhuma rotina de backup hoje.

## Pessoa afetada ou beneficiada

Marcio, responsável por não perder dados reais das pessoas usuárias durante o Beta.

## Resultado ou valor esperado

Existe um snapshot diário do banco de produção com retenção definida, permitindo restaurar dados em caso de falha ou perda.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decidido por Marcio em 2026-09-28: backup automático já deste o Beta, não adiado para um marco futuro. Depende do Postgres de produção (item de dockerização) já estar de pé.

## Referências relacionadas

- Nenhuma referência relevante encontrada.

## Comportamento esperado

Estado em 2026-10-13: o stack de produção (SPEC-0022) roda o Postgres como serviço do Swarm, com volume local na VPS; o backend e o worker já usam o Cloudflare R2 para os uploads e arquivos.

- **Destino (Pergunta 1, 2026-10-13):** o dump diário é copiado para um bucket do Cloudflare R2 separado do bucket do sistema, com credencial própria; o backup precisa sobreviver à perda da VPS.
- **Retenção (Pergunta 2):** 7 backups diários e 4 semanais.
- **Proteção (Pergunta 3):** o dump é cifrado antes de ir ao R2; a chave fica com a pessoa responsável, fora da VPS (por exemplo, no gerenciador de senhas), e o job recebe uma cópia como secret do Swarm; o runbook (0032) diz onde a chave está guardada.
- **Cobertura (Pergunta 4, opção 3):** só o Postgres; os vetores do Qdrant são derivados e refeitos pela Fase 2 a partir dos `.md`. A entrega confere que os arquivos de origem e os `.md` ficam no R2, fora da VPS (conferido no código: backend e worker usam `r2_credentials`).
- **Verificação (Pergunta 5, opção 3):** cada backup é verificado ao terminar (o arquivo existe, o tamanho é coerente e a cifragem abre com a chave). O teste automático semanal de restauração fica como evolução.
- **Aviso de falha (Pergunta 6, opção 4):** falha do backup ou da verificação avisa por e-mail e por mensagem num canal de chat (webhook); o sucesso fica só no registro do job.
- **Horário (Pergunta 7):** de madrugada (por exemplo, 3h), com o sistema no ar; `pg_dump` sem parar a aplicação. A frequência pode subir depois.
- **Restauração (Pergunta 8, opção 3):** um script de restauração (baixa o dump escolhido do R2, decifra com a chave e restaura num Postgres), o passo a passo no runbook (0032) e uma restauração de teste num banco temporário na entrega, uma única vez.

## Regras de negócio

- Nenhuma credencial, chave de cifragem ou destino é versionado.
- O backup nunca é guardado só na VPS.
- Nenhum comando de restauração roda contra o banco de desenvolvimento ou de teste; a restauração de teste usa um banco temporário próprio.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — bloqueante. O backup precisa do Postgres de produção já definido como serviço do Swarm.

## Situações de erro

- Falha ao gerar, cifrar ou enviar o dump, ou verificação reprovada: aviso por e-mail e por chat; o backup anterior permanece.
- Chave de cifragem perdida: o backup não pode ser restaurado; por isso a chave fica fora da VPS e o runbook registra onde.
- R2 indisponível: o job avisa a falha e tenta de novo na execução seguinte (a detalhar na spec).

## Escopo

- Dentro: job diário de dump cifrado para o R2, retenção de 7 diários e 4 semanais, verificação a cada backup, aviso de falha por e-mail e chat, script de restauração e uma restauração de teste na entrega.
- Fora: backup do Qdrant; recuperação até um ponto no tempo (PITR) e réplica; teste automático periódico de restauração; frequência maior que a diária.

## Dúvidas, decisões e riscos

- Decisões das Perguntas 1 a 8 de 2026-10-13, registradas em "Comportamento esperado". Área de perguntas encerrada no limite de oito.
- Em aberto: provedor do e-mail e do canal de chat para os avisos; nome do bucket e escopo da credencial do R2; ferramenta de cifragem; onde o job roda (serviço agendado no Swarm ou tarefa do worker).
- Risco: chave perdida inutiliza o backup; mitigado por guardá-la fora da VPS.
- Risco: 24 horas de perda máxima, por causa da frequência diária; aceito no Beta (hipótese dependente de uso real).
- Verificação real do envio ao R2 e do aviso só no ambiente de produção (mesmo limite da SPEC-0022).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
