# Backlog: Gestão de secrets de produção via Docker Swarm

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0030 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Deploy em Beta (Docker Swarm) |
| Funcionalidade | Provisionamento e conferência dos secrets de produção |
| Tipo | Técnico |
| Prioridade | Não priorizado |
| Milestones | M03 |
| Criado em | 2026-09-28 |
| Spec promovida | specs/planned/0027-provisionamento-de-secrets-do-swarm/spec.md (SPEC-0027, Planned) |

## Ideia original

Gerir as credenciais de produção (OpenRouter, Cloudflare R2, senha do Postgres, segredo de sessão, etc.) por docker secrets do Swarm, em vez de arquivo .env em texto puro no servidor.

## Problema percebido

Hoje as credenciais ficam em arquivos .env locais, adequado para desenvolvimento mas não para um servidor de produção compartilhado pela equipe.

## Pessoa afetada ou beneficiada

Marcio, ao operar e atualizar o ambiente de produção durante o Beta.

## Resultado ou valor esperado

Nenhuma credencial de produção fica em texto puro no stack file nem versionada; segredos são injetados nos serviços via docker secrets.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decorrente da escolha de hospedagem feita por Marcio em 2026-09-28.

**Estado observado em 2026-10-08 (análise do repositório, não declaração da pessoa):** a SPEC-0022 já fez `deploy/stack.prod.yml` consumir secrets externos do Swarm (`openrouter_api_key`, `r2_credentials`, `session_secret`, `postgres_password`) e a SPEC-0026 acrescentou `conexoes_chave`. Nenhuma credencial fica em texto puro na stack, e um secret ausente impede o serviço de subir (teste automatizado). A SPEC-0022 deixou expressamente para este item a "criação dos docker secrets em si e seu conteúdo real". O que falta, portanto, é o processo de criar, conferir e trocar esses secrets no servidor.

## Referências relacionadas

- `specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md` — spec relacionada: stack consome os secrets; criação dos secrets ficou para este item (seção de fora de escopo).
- `specs/completed/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` — spec relacionada: introduziu o secret `conexoes_chave` (DEC-012) e a regra de que trocar a chave de cifra exige recadastrar as conexões.
- `deploy/stack.prod.yml`, `deploy/stack.local.yml`, `deploy/build_and_deploy.sh`, `tests/test_deploy_stack.py` — evidência local do estado atual.
- `specs/backlog/0032-runbook-de-deploy-manual-em-producao.md` — backlog relacionado: depende deste; o runbook referenciará o script.
- `specs/backlog/0031-backup-automatico-do-postgres-de-producao.md` — backlog relacionado: credenciais de backup, se houver, entram em item próprio.
- `.specsfy/RULES.md` — regras de segredo somente escrita e de URL de conexões (SPEC-0026).

## Comportamento esperado

- **Decisão (2026-10-08, Marcio):** a entrega principal é um script em `deploy/` que cria e troca os secrets do Swarm lendo cada valor **sem eco** (sem passar pelo histórico do shell nem por arquivo em disco), mais uma **verificação prévia** em `deploy/build_and_deploy.sh` que falha antes do deploy se algum secret estiver ausente. Inventário com data de criação e lembrete de troca periódica ficam **fora**.
- **Decisão:** a troca de um secret usa **nome versionado** (ex.: `openrouter_api_key_v2`). O stack aponta para a versão atual por uma variável definida no momento do deploy; o serviço é atualizado em rolling update e o secret antigo é preservado até a troca ser confirmada.
- **Decisão:** `session_secret`, `postgres_password` e `conexoes_chave` são **gerados** pelo script (aleatórios fortes; `conexoes_chave` no formato Fernet) e cada valor é exibido **uma única vez**, na criação, para ser guardado no gerenciador de senhas. Somente `openrouter_api_key` e `r2_credentials` são pedidos ao operador, sem eco.
- **Decisão:** a troca de `postgres_password` e de `conexoes_chave` é **bloqueada por padrão**. Só acontece com parâmetro explícito e confirmação digitada, depois de o script mostrar a consequência e o procedimento manual (Postgres: alterar a senha dentro do banco antes do rolling update; conexões: todas as chaves precisam ser recadastradas).
- **Decisão:** `session_secret` é **removido** da stack, do teste da stack e do script: nada em `src/` o usa desde a SPEC-0020 (sessões usam token opaco com hash).
- **Decisão:** o script também prepara o **ensaio local** (`deploy/stack.local.yml`): um parâmetro de ambiente local cria os secrets com sufixo `_local` e valores fictícios gerados, sem pedir chave real, e o ensaio passa a usar o mesmo mecanismo de versão do nome.

## Regras de negócio

- O valor de um secret nunca aparece em argumento de comando, histórico do shell, log, saída de erro, arquivo versionado ou stack file.
- Um secret já criado não é sobrescrito: criar um nome existente falha; trocar sempre cria uma nova versão.
- Somente o operador com acesso ao manager do Swarm executa o script (uso manual nesta fase, sem CI/CD).
- A verificação prévia confere a **existência** dos secrets referenciados (o Swarm não devolve o conteúdo); a validade do conteúdo é checada na criação (por exemplo, formato Fernet da chave de cifra).

## Critérios de aceitação

- **Criar pela primeira vez:** Given um Swarm sem os secrets; When o operador executa o script para produção; Then são criados `openrouter_api_key`, `r2_credentials`, `postgres_password` e `conexoes_chave` (os dois primeiros pedidos sem eco; `postgres_password` e `conexoes_chave` gerados e exibidos uma única vez) e nenhum valor fica em histórico, log ou arquivo.
- **Verificação prévia bloqueia:** Given um secret referenciado ausente; When `build_and_deploy.sh` roda; Then ele falha antes de `docker stack deploy`, lista os secrets ausentes e o comando para criá-los.
- **Troca versionada:** Given `openrouter_api_key` em uso; When o operador troca a chave; Then nasce `openrouter_api_key_v2`, o stack passa a apontar para ela no próximo deploy, o serviço atualiza em rolling update e a versão anterior continua existindo.
- **Troca perigosa bloqueada:** Given `postgres_password` ou `conexoes_chave`; When o operador pede a troca sem o parâmetro explícito; Then o script recusa e mostra a consequência; com o parâmetro e a confirmação digitada, mostra o procedimento e só então prossegue.
- **Segredo repetido recusado:** Given um secret que já existe; When o operador tenta criá-lo de novo; Then o script falha sem alterar o existente.
- **Ensaio local:** Given o parâmetro de ambiente local; When o script roda; Then cria os secrets `_local` com valores fictícios sem pedir chave real, e o ensaio local sobe usando-os.
- **Sem `session_secret`:** Given a stack atualizada; When os testes da stack rodam; Then nenhum serviço referencia nem exporta `session_secret` e o backend continua funcionando.

## Qualidades e operação

- Segurança: vazamento zero do valor em histórico, log e saída; permissão mínima (script só no manager); `conexoes_chave` perdida obriga recadastrar as conexões, por isso o valor é exibido uma vez para guarda externa.
- Privacidade: não aplicável — são credenciais de infraestrutura, sem dado pessoal.
- Desempenho e volume: não aplicável (execução manual e rara).
- Auditoria e observabilidade: o script informa o que criou ou recusou, por nome e versão, nunca por valor.
- Testabilidade: o script e a verificação são exercitados em testes com um `docker` simulado no `PATH`, sem Swarm real; o ensaio local confirma o caminho real.

## Dependências

- `specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md` — satisfeita: a stack de produção e seu consumo de secrets existem.
- `specs/completed/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` — satisfeita: define o secret `conexoes_chave`.
- Acesso ao manager do Swarm com a CLI do Docker, no momento do uso (operacional, não de desenvolvimento).
- Este item bloqueia o deploy da SPEC-0026 em produção (o secret `conexoes_chave` precisa existir) e alimenta `specs/backlog/0032-runbook-de-deploy-manual-em-producao.md`.

## Situações de erro

- Secret referenciado ausente na verificação prévia → deploy bloqueado com a lista e o comando de criação.
- Secret já existente → criação recusada sem efeito colateral.
- Entrada vazia ou formato inválido (por exemplo, chave Fernet malformada) → recusa na criação, sem criar nada.
- Docker indisponível ou nó que não é manager → mensagem clara e saída com erro, sem valores.
- Interrupção no meio de uma troca → o secret antigo permanece em uso; nada fica pela metade.
- Troca de `postgres_password` ou `conexoes_chave` sem parâmetro explícito → recusada com a consequência.

## Escopo

- Dentro: script de criação e troca de secrets em `deploy/`; verificação prévia em `build_and_deploy.sh`; nome versionado resolvido por variável no stack; remoção do `session_secret`; suporte ao ensaio local; testes com `docker` simulado; atualização de `.specsfy/RULES.md`, `STACK.md` (se aplicável) e da documentação.
- Fora: gerenciadores externos de segredo (Vault, KMS); inventário com datas e lembrete de troca; rotação automática ou agendada; credenciais de backup (BACKLOG-0031); automação por CI/CD; o runbook completo de deploy (BACKLOG-0032), que apenas referenciará o script.

## Dúvidas, decisões e riscos

- **Resolvidas (2026-10-08):** entrega principal (script mais verificação), troca por nome versionado, geração dos secrets internos, bloqueio da troca de `postgres_password` e `conexoes_chave`, remoção do `session_secret` e suporte ao ensaio local (ver Comportamento esperado).
- **Risco:** trocar `postgres_password` só no Swarm derruba backend e worker, porque o Postgres não relê o secret depois de criado; mitigado pelo bloqueio por padrão.
- **Risco:** valor gerado e exibido uma vez pode ser perdido; mitigado pela instrução de guarda no gerenciador de senhas. Para `conexoes_chave` a perda obriga recadastrar as conexões.
- **Hipótese a verificar na spec:** a forma exata de resolver o nome do secret por variável no Compose 3.7 (campo `name:` do secret externo) e a compatibilidade com o override local.
- **Interface para pessoas:** não — é ferramenta de linha de comando operada por Marcio; nenhuma tela é criada ou alterada.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Seguir para `$specsfy-03-specify` e produzir a spec inicial; o refinamento fechou seis perguntas na área de segurança e operação (limite de oito).

## Registro das respostas — 2026-10-08

Respostas literais “1” às seis perguntas, normalizadas em Comportamento esperado: (1) script mais verificação prévia, (2) troca por nome versionado, (3) geração dos secrets internos com exibição única, (4) bloqueio da troca de `postgres_password` e `conexoes_chave`, (5) remoção do `session_secret`, (6) suporte ao ensaio local com valores fictícios. Área Segurança e operação: 6 de 8 perguntas usadas; nenhuma lacuna aplicável restante. Interface: não aplicável.
