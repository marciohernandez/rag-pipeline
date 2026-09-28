# Backlog: Chat com assistente LLM para ajudar no uso do sistema

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0022 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-18 |
| Spec promovida | specs/defined/0021-chat-assistente-especialista-rag-pipeline/spec.md (SPEC-0021, fatia 1) |

## Ideia original

Ter um chat com um modelo de LLM que ajuda o usuario na utilização do sistema inicialmente e depois podemos pensar em outras açoes que ele pode ter. Quero que o sistema esteja com IA integrada de ponta a ponta ("IA first" ou conceito parecido).

## Problema percebido

Não identificado no texto original. Inferência: pessoas usuárias podem ter dificuldade para descobrir ou operar as funcionalidades do sistema (Workspaces, Bases, execuções, consultas) sem orientação guiada.

## Pessoa afetada ou beneficiada

Não identificado no texto original. Inferência: pessoas usuárias do sistema (owner/admin/member) que interagem com Workspaces e Bases.

## Resultado ou valor esperado

Uma pessoa consegue conversar com um assistente de IA especializado em RAG e em todo o pipeline (recebimento de documentos, chunking, embeddings, upsert no banco vetorial), que a orienta sobre a melhor forma de processar os documentos que ela tem (ex.: "qual a melhor forma de fazer o processamento dos documentos que tenho?", "é melhor o text splitter ou o markdown splitter para meus documentos, para ter um melhor RAG?"). Esse assistente pode ganhar outras ações no futuro (hoje é só orientação/recomendação, sem agir sozinho), dentro de uma direção mais ampla de IA integrada ao produto.

## Contexto

**Correção registrada em 2026-09-18**: a formulação inicial ("copiloto geral para qualquer assunto") foi corrigida pela pessoa usuária para um escopo mais específico — um especialista em RAG e em todo o processo do pipeline, não um assistente aberto a qualquer tema nem um simples guia de navegação de telas.

Distingue-se de `chat.py` (CLI de demonstração do RAG, que consulta o conteúdo indexado de uma Base para responder perguntas sobre esse conteúdo): este assistente aconselha sobre a estratégia de processamento em si (chunking, splitter, embeddings), não sobre o conteúdo já indexado. Relaciona-se com BACKLOG-0010 (provider de LLM plugável), que já planeja um contrato `LLMProvider` neutro reutilizável por este chat, e com o BACKLOG-0025 (campos de estratégia de chunking — splitter, tamanho, overlap — e nome de coleção na interface de upload, que a SPEC-0019 chamava de "item 0023"; ainda não especificado): este assistente pode ser o mecanismo que ajuda a pessoa a decidir esses mesmos campos, em vez de preenchê-los às cegas.

## Referências relacionadas

- `specs/backlog/0010-provider-llm-plugavel.md` — planeja um contrato `LLMProvider` neutro, adapter OpenAI e factory para a família de LLM de chat/geração; este item poderia reutilizar esse contrato em vez de acoplar a um SDK específico. Tipo: backlog relacionado.
- `chat.py` — CLI de demonstração já existente que conversa com um LLM sobre o conteúdo indexado de uma Base (RAG). Tipo: documentação/contexto relacionado (superfície próxima, propósito diferente: conteúdo da Base, não orientação de uso do produto).
- `specs/backlog/0003-modularizar-providers-factory-adapter.md` — estabelece o padrão plug and play (`src/providers/`) do qual BACKLOG-0010 deriva. Tipo: backlog relacionado (pré-requisito indireto).
- `specs/backlog/0025-expor-configuracoes-de-ingestao-na-interface.md` — campos de estratégia de chunking (splitter, tamanho, overlap) e coleção na interface de upload; a SPEC-0019 (`specs/completed/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md`) o citava como "item 0023", número depois ocupado pela autenticação por pessoa. Tipo: backlog relacionado (mesmo domínio de decisão — este item pode ser o meio de decidir esses campos, não a interface bruta deles).
- `src/pipeline/chunker.py`, `config.yaml` — splitters e parâmetros de chunk hoje configuráveis apenas por config global/frontmatter, sem recomendação assistida. Tipo: superfície técnica afetada.

## Comportamento esperado

- Chat disponível em todas as páginas do sistema (não preso a uma tela), com opção de abrir uma nova conversa e um histórico de conversas anteriores para retomar.
- Conversa livre por padrão sobre estratégia de RAG e do pipeline (chunking, splitter, embeddings, upsert); a pessoa pode opcionalmente apontar uma Base/documento existente para uma análise mais precisa do conteúdo real antes de recomendar.
- Fonte de conhecimento sobre "o que o sistema faz": documentação viva mantida pelo framework (`docs/`, `PROJECT.md`, `INTERFACE.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`), indexada via RAG — não acessa código-fonte diretamente.
- Memória de curto prazo (dentro da mesma conversa) e de longo prazo (atravessa conversas diferentes, guardando preferências e fatos conversados antes) — nos moldes da memória do Claude. A memória de longo prazo é por pessoa individual, não por tenant/projeto — depende de BACKLOG-0023 (autenticação real por pessoa).
- Nesta fatia, o assistente apenas orienta/recomenda; não executa ações no sistema em nome da pessoa (ex.: não cria Base nem altera configuração sozinho). Ações futuras ficam para uma evolução posterior, fora de escopo aqui.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- **Dado** uma pessoa autenticada em qualquer tela do sistema, **quando** ela abre o assistente, **então** consegue conversar livremente sobre estratégia de RAG/pipeline e ver o histórico de conversas anteriores, com opção de iniciar uma nova.
- **Dado** uma pergunta sobre a melhor forma de processar documentos, **quando** a pessoa não aponta nenhuma Base/documento, **então** o assistente responde com base na descrição textual dada, sem inventar recursos inexistentes do produto (grounded na documentação via RAG).
- **Dado** a mesma pergunta, **quando** a pessoa aponta uma Base/documento existente, **então** o assistente examina o conteúdo real antes de recomendar splitter/chunking.
- **Dado** um assistente com memória de longo prazo (fatia 2, após BACKLOG-0023), **quando** a pessoa pergunta em uma nova conversa algo relacionado a uma preferência ou fato já conversado antes, **então** o assistente usa essa memória sem repetir a pergunta.
- **Dado** a mesma fatia 2, **quando** a pessoa acessa a área de memória, **então** consegue visualizar e apagar itens individuais guardados sobre ela.
- **Dado** qualquer resposta do assistente, **quando** ele não executa nenhuma ação no sistema, **então** nenhuma Base, Workspace, execução ou configuração é criada/alterada/apagada por ele nesta entrega.

## Qualidades e operação

- Segurança: a avaliar na especificação (ex.: escopo de leitura da Base apontada para análise deve respeitar o isolamento por tenant/projeto já existente).
- Privacidade: a pessoa deve conseguir ver e apagar itens de memória de longo prazo guardados sobre ela (decisão confirmada, fatia 2); conteúdo de documentos apontados para análise aprofundada é enviado ao provider de LLM configurado, mesmo padrão já aceito hoje por `chat.py`.
- Desempenho e volume: a avaliar na especificação.
- Auditoria e observabilidade: a avaliar na especificação.

## Dependências

- `specs/backlog/0023-autenticacao-real-por-pessoa.md` — bloqueante. A memória de longo prazo (preferências e histórico entre conversas diferentes) só pode ser implementada por identidade individual depois que essa autenticação existir; sem ela, este item não tem "de quem" guardar a memória de longo prazo.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro (fatia 1, sem depender de BACKLOG-0023): chat disponível em todas as páginas, com histórico de conversas e opção de nova conversa; conversa livre especializada em RAG/pipeline (chunking, splitter, embeddings, upsert); análise aprofundada quando a pessoa aponta uma Base/documento existente; memória de curto prazo (só dentro da mesma conversa); base de conhecimento via RAG sobre a documentação viva do produto.
- Dentro (fatia 2, depende de BACKLOG-0023): memória de longo prazo por pessoa individual, atravessando conversas diferentes (preferências e fatos conversados antes, nos moldes da memória do Claude).
- Fora (nesta entrega, ambas as fatias): o assistente executar ações no sistema em nome da pessoa (criar/alterar/apagar Workspace, Base, execução); isso é uma direção futura explicitamente adiada pela própria ideia original. Também fora: escolha do provider de LLM em si (depende de BACKLOG-0010).

## Dúvidas, decisões e riscos

- **Decisão**: escopo é um copiloto especialista em RAG/pipeline (não um guia genérico de navegação nem um assistente aberto a qualquer assunto) — corrigido pela pessoa usuária em 2026-09-18.
- **Decisão**: conversa livre por padrão; análise de conteúdo real só quando a pessoa aponta uma Base/documento existente (não obrigatório em toda pergunta).
- **Decisão**: fonte de conhecimento sobre o produto é a documentação viva via RAG (`docs/`, `PROJECT.md`, `INTERFACE.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`), não código-fonte.
- **Decisão**: chat disponível em todas as páginas, com histórico de conversas e opção de nova conversa.
- **Decisão**: memória de curto prazo (fatia 1) e de longo prazo por pessoa individual (fatia 2, após BACKLOG-0023).
- **Decisão**: fatiar em duas entregas — fatia 1 não espera BACKLOG-0023; fatia 2 (memória de longo prazo) depende dele.
- **Decisão**: fatia 2 dá à pessoa controle de visualizar e apagar itens de memória guardados sobre ela.
- **Decisão**: nesta entrega (ambas as fatias) o assistente só orienta/recomenda — não executa ações no sistema.
- **Risco**: BACKLOG-0023 (autenticação real por pessoa) afeta todo o produto, não só este item; specs futuras que usam `Identity(tenant_id, project_id, role)` precisarão decidir se/como incorporam a pessoa individual quando essa mudança chegar.
- **Aberto**: qual provider de LLM usar (depende de BACKLOG-0010, ainda não refinado); pode herdar a mesma decisão ou seguir independente — a esclarecer na especificação da fatia 1.
- **Aberto**: quais papéis (owner/admin/member) têm acesso ao assistente — assumido "todos", por ser só orientação sem ação; a confirmar na especificação.
- **Aberto**: formato de armazenamento e extração de memória de longo prazo (que tipo de fato/preferência vira memória, como é resumido) — fica para a especificação da fatia 2, depois de BACKLOG-0023.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras (acesso por papel ainda a confirmar).
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco (fatia 2).
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Fatia 1 pronta para `$specsfy-03-specify` (chat, conversa livre, análise de Base apontada, memória de curto prazo, sem BACKLOG-0023). Fatia 2 (memória de longo prazo por pessoa) só pode ser especificada depois que BACKLOG-0023 (autenticação real por pessoa) estiver definido.

**Atualização em 2026-09-28**: fatia 1 entregue pela SPEC-0021 (mesclada em `main`). BACKLOG-0023 concluído (SPEC-0020, mesclada em `main`). A fatia 2 foi extraída para `specs/backlog/0027-memoria-de-longo-prazo-do-assistente-por-pessoa.md`, que preserva o escopo, os critérios de aceite e as decisões desta seção.
