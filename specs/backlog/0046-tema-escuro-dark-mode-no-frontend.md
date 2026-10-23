# Backlog: Tema escuro (dark mode) no frontend

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0046 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | Interface — escolha de tema |
| Tipo | Melhoria |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-05 |
| Spec promovida | specs/defined/0024-tema-escuro-dark-mode-no-frontend/spec.md (SPEC-0024) |

## Ideia original

e já quero ter a opção dark no sistema

## Problema percebido

O frontend só tem o tema claro: o globals.css já define as variáveis do tema .dark, mas nada aplica a classe nem há como a pessoa escolher o tema.

## Pessoa afetada ou beneficiada

Pessoas usuárias do sistema (Marcio e a equipe de consultoria); beneficiada por poder escolher o tema (inferência, não declarada pelo usuário).

## Resultado ou valor esperado

A pessoa escolhe entre Claro, Escuro e Sistema e o sistema lembra a escolha no navegador.

## Contexto

Item de melhoria de interface surgido no ensaio local do stack de produção (M03), em 2026-10-05. Não pertence à condição de saída do M03 (deploy em Beta), por isso não está vinculado a um marco.

Estado observado no frontend (Next.js, React, Tailwind v4, shadcn/ui, Vitest):

- `frontend/src/app/globals.css` define as variáveis do tema escuro em `.dark` e o `@custom-variant dark (&:is(.dark *))`.
- Nada aplica a classe `.dark` ao `<html>`: o `frontend/src/app/layout.tsx` raiz não tem controle nem preferência salva.
- As telas autenticadas compartilham `frontend/src/app/(autenticado)/layout.tsx`, com o menu da pessoa (`features/auth/MenuPessoa`, sobre o `dropdown-menu` do shadcn/ui) e o botão do Assistente.
- `/login` e `/nova-senha` ficam fora desse layout.

## Referências relacionadas

- `INTERFACE.md` — mapa do design system; aponta `globals.css` como fonte de tokens e tema. Tipo: documentação relacionada.
- `DESIGNSYSTEM.MD` — defaults macro de interface. Tipo: documentação relacionada.
- `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx`, `frontend/src/app/(autenticado)/layout.tsx`, `frontend/src/features/auth/MenuPessoa.tsx` — superfícies técnicas afetadas.
- Busca por duplicatas em Inbox, backlog, specs e docs em 2026-10-05: nenhuma possível duplicata.

## Respostas confirmadas na descoberta

Interface (5 de 8 perguntas usadas; área resolvida, sem lacuna aplicável aberta):

1. **Modos de tema** — Três opções: Claro, Escuro e Sistema. "Sistema" acompanha o tema do computador e é o padrão inicial. (Resposta 1.)
2. **Onde fica o controle** — No menu da pessoa (`MenuPessoa`), nas telas autenticadas. Em `/login` e `/nova-senha`, o tema segue o do sistema, sem controle. (Resposta 1.)
3. **Onde a escolha é guardada** — Só no navegador. A preferência por conta da pessoa fica registrada como evolução futura, fora do escopo desta entrega. (Resposta 3.)
4. **Cobertura nas telas existentes** — Todas as telas atuais ficam corretas nos dois temas: workspaces, execuções e consulta, pessoas, projeto, diálogos, painel do Assistente, login e nova senha. Isso inclui ajustar as cores onde algum componente ficar ilegível. (Resposta 1.)
5. **Critérios de qualidade** — Os três juntos: sem "piscar" no tema errado ao carregar a página; contraste legível (WCAG AA) nos dois temas; controle operável por teclado e identificado para leitores de tela. (Resposta 1.)

## Comportamento esperado

- O menu da pessoa oferece a escolha entre Claro, Escuro e Sistema, indicando a opção ativa.
- Com Sistema, o tema acompanha o do computador e muda junto com ele.
- A escolha vale para todas as telas autenticadas e é lembrada ao recarregar e ao voltar ao sistema no mesmo navegador.
- Sem escolha prévia, o padrão é Sistema.
- `/login` e `/nova-senha` seguem o tema do sistema e não têm controle.

## Regras de negócio

- A preferência é por navegador e não é enviada ao backend.
- Se o navegador não permitir guardar a escolha (armazenamento bloqueado), o sistema segue o tema do sistema e não exibe erro.
- Nenhuma tela existente muda de conteúdo, rota ou permissão; só a aparência.

## Critérios de aceitação

- **Escolha e persistência.** Given uma pessoa autenticada sem escolha prévia; When ela abre o menu da pessoa e seleciona Escuro; Then todas as telas autenticadas aparecem no tema escuro, e ao recarregar a página o tema escuro continua ativo.
- **Seguir o sistema.** Given uma pessoa com a opção Sistema ativa e o computador no tema escuro; When ela abre o sistema; Then o tema escuro é aplicado, e se o computador mudar para o claro, o sistema acompanha sem recarregar.
- **Sem piscar.** Given uma pessoa com Escuro salvo; When ela recarrega qualquer tela autenticada; Then a página nunca é exibida em tema claro antes de passar para o escuro.
- **Telas de acesso.** Given o computador no tema escuro; When uma pessoa abre `/login` ou `/nova-senha`; Then a tela aparece no tema escuro e não há controle de tema nela.
- **Legibilidade.** Given o tema escuro ativo; When se percorrem workspaces, execuções e consulta, pessoas, projeto, diálogos e painel do Assistente; Then textos, bordas e estados de foco atendem ao contraste WCAG AA.
- **Teclado e leitor de tela.** Given o menu da pessoa aberto; When a pessoa navega só pelo teclado; Then consegue alcançar, escolher e confirmar cada opção de tema, e cada opção é anunciada com seu nome e se está ativa.
- **Armazenamento indisponível.** Given um navegador que bloqueia o armazenamento local; When a pessoa escolhe um tema; Then o tema muda na sessão atual e, ao recarregar, o sistema volta a seguir o tema do sistema, sem mensagem de erro.

## Qualidades e operação

- Segurança: sem impacto; a preferência não é dado sensível nem sai do navegador.
- Privacidade: nenhum dado pessoal; nada é enviado ao backend.
- Desempenho e volume: aplicar o tema antes da primeira renderização, sem atraso perceptível.
- Auditoria e observabilidade: não se aplica.
- Acessibilidade: contraste WCAG AA nos dois temas; teclado; leitor de tela (ver critérios).

## Dependências

- Nenhuma dependência de backend ou de outro item de backlog.
- A escolha de biblioteca ou mecanismo para o tema (por exemplo, `next-themes` ou solução própria) é decisão técnica da spec e não está definida aqui.

## Situações de erro

- Armazenamento local bloqueado ou indisponível: o sistema segue o tema do sistema, sem erro visível.
- Valor salvo inválido ou desconhecido: tratado como "Sistema".

## Escopo

- Dentro: escolha entre Claro, Escuro e Sistema no menu da pessoa; persistência no navegador; aplicação sem "piscar"; ajuste de cores nos componentes das telas existentes; `/login` e `/nova-senha` seguindo o tema do sistema; testes.
- Fora: preferência por conta da pessoa (evolução futura); temas além de Claro e Escuro; redesenho de telas; controle de tema em `/login` e `/nova-senha`; troca da rota `/` (hoje a página-modelo do Next.js), que não faz parte desta entrega.

## Dúvidas, decisões e riscos

- Decisões: ver "Respostas confirmadas na descoberta".
- Nenhuma lacuna aplicável aberta.
- Risco: componentes com cores fixas (sem usar as variáveis do tema) podem ficar ilegíveis no escuro; a revisão visual da spec deve percorrer todas as telas e estados.
- Ponto levantado e fora de escopo: a rota `/` ainda exibe a página-modelo do Next.js; tratar em item próprio.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Spec criada em 2026-10-05 e definida no mesmo dia: `specs/defined/0024-tema-escuro-dark-mode-no-frontend/spec.md` (SPEC-0024). A spec usa o número 0024 porque a SPEC-0023 já existe em uma branch remota ainda não integrada. A partir daqui, a fonte normativa é a spec; este item preserva apenas a proveniência.
