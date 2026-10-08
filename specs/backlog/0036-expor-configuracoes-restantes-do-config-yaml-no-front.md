# Backlog: Expor no front as configurações restantes do config.yaml

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0036 |
| Status | Ready for specification |
| Produto | rag-pipeline |
| Épico | Configuração do processamento pelo front |
| Funcionalidade | Fluxo de Nova Base |
| Tipo | Melhoria |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-08 |
| Spec promovida | Nenhuma |

## Ideia original

eu preciso que esteja tudo no front [...] todas as configuração que faço para definir todo o processamento até subir, escolher nome de coleção etc eu preciso que eu tenha a opção de definir no front. [...] eu quero fazer agora esse parte de expor no front todas as configurações do .ymal (Fonte: specs/inbox/2026-10-08-205918-expor-no-front-todas-as-configuracoes-do-config-yaml.md)

## Problema percebido

Parte das configurações que definem o processamento só existe no config.yaml (resumos de seção, headers de divisão, qualidade mínima, status bloqueados, batch_size, sync_mode, namespace, index_name); ajustá-las exige editar arquivo fora do front.

## Pessoa afetada ou beneficiada

Owner/admin que opera o pipeline pelo front e testa o processamento real.

## Resultado ou valor esperado

Definir pelo front todo o processamento relevante, do arquivo até a coleção no Qdrant, sem editar config.yaml.

## Contexto

SPEC-0026 já expõe splitter, tamanho, overlap, conexões (modelo e dimensões do embedding), coleção e dimensão. Esta entrega cobre o restante que muda o resultado do processamento. Precedente: BACKLOG-0025 (Promoted).

## Referências relacionadas

- `specs/inbox/2026-10-08-205918-expor-no-front-todas-as-configuracoes-do-config-yaml.md` — captura de origem (preservada).
- `specs/backlog/0025-expor-configuracoes-de-ingestao-na-interface.md` — precedente (Promoted para SPEC-0026).
- `specs/completed/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` — spec relacionada: etapas, conexões e itens fora de escopo.
- `specs/completed/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md` — spec relacionada: coleção por Base.
- `specs/backlog/0035-apagar-base-usa-colecao-e-conexoes-da-base.md` — backlog relacionado: bug de exclusão, prioridade anterior.
- `config.yaml` — evidência das chaves existentes.
- `specs/inbox/2026-10-08-214501-dropdown-da-etapa-divisao-com-texto-e-fundo-da-mesma-cor-no-tema-escuro.md` — defeito incorporado a este item.
- `specs/inbox/2026-10-08-215112-rascunho-do-fluxo-de-nova-base-conexao-sem-sair-do-fluxo-e-ajustes-da-previa.md` — origem dos ajustes da Prévia e do cadastro de conexão no fluxo; o rascunho fica fora deste item.

## Comportamento esperado

No fluxo de Nova Base (`/workspaces/[id]/bases/nova`), a pessoa define pelo front, além do que a SPEC-0026 já oferece: resumos de seção (ligar/desligar e mínimo de subseções) e headers de divisão na etapa Divisão; mínimo útil e status bloqueados em um bloco Qualidade na Divisão; `batch_size`, `sync_mode`, `namespace` e `index_name` na Publicação; campos pouco usados em um bloco Avançado recolhido. Os valores iniciais vêm do `config.yaml`, a Prévia reflete as escolhas de divisão, e a Base guarda os valores usados.

Na Prévia, as ações Voltar e Próxima ficam no topo da etapa, e a pessoa escolhe quantos chunks ver por página (10, 20, 50, 75 ou 100). Na Publicação, quando falta conexão, a pessoa cadastra a conexão de embeddings ou de Qdrant num painel lateral sem sair do fluxo. Os seletores das etapas ficam legíveis nos dois temas.

## Regras de negócio

- As configurações valem por Base; o `config.yaml` fornece só o padrão inicial.
- Bases anteriores mantêm o comportamento atual (sem valores guardados, vale o padrão).
- A Prévia usa as mesmas escolhas de divisão, resumos e headers que a publicação.
- `sync_mode` padrão `mirror`, com aviso; o backend rejeita valores que a política de segurança não aceita.
- Valores inválidos ou fora dos limites são recusados com mensagem clara, antes de gerar embeddings.
- Segredos continuam só nas conexões cifradas; nenhuma configuração nova carrega segredo.
- Validação (`limiar_minimo`, `top_k`), log e caminhos não entram.

## Critérios de aceitação

- **Dado** o fluxo de Nova Base, **quando** a pessoa abre a etapa Divisão, **então** vê resumos de seção, headers e o bloco Qualidade pré-preenchidos com o padrão do `config.yaml`.
- **Dado** que a pessoa desliga os resumos de seção, **quando** calcula a Prévia, **então** nenhum chunk-resumo aparece e a publicação gera os mesmos chunks.
- **Dado** que a pessoa altera os headers de divisão, **quando** calcula a Prévia, **então** a divisão segue os novos títulos.
- **Dado** a etapa Publicação, **quando** a pessoa define `batch_size`, `sync_mode`, `namespace` e `index_name` e publica, **então** a execução usa esses valores e a Base os guarda.
- **Dado** uma Base anterior a esta entrega, **quando** é repetida, **então** o comportamento não muda.
- **Dado** uma Prévia com muitos chunks, **quando** a pessoa escolhe 50 por página, **então** a lista mostra 50 chunks e a paginação recalcula o total de páginas.
- **Dado** a etapa Prévia, **quando** a pessoa está em qualquer ponto da lista, **então** consegue acionar Próxima e Voltar no topo da etapa sem rolar até o fim.
- **Dado** a etapa Publicação sem conexão de embeddings, **quando** a pessoa cadastra uma conexão no painel lateral, **então** o painel fecha, a conexão aparece selecionada e os arquivos e configurações das etapas anteriores continuam na tela.
- **Dado** o tema escuro, **quando** a pessoa abre qualquer seletor das etapas Divisão e Publicação, **então** todas as opções ficam legíveis, com texto e fundo contrastantes.
- **Dado** um valor inválido (ex.: `batch_size` 0 ou `sync_mode` desconhecido), **quando** a pessoa tenta avançar ou publicar, **então** a tela mostra o erro em linha e nada é gravado no Qdrant.

## Qualidades e operação

- Segurança: validar no backend; `sync_mode` passa pela política de segurança; só owner/admin.
- Privacidade: nenhuma configuração nova carrega dado pessoal ou segredo.
- Desempenho e volume: `batch_size` com limite máximo definido na spec.
- Auditoria e observabilidade: registrar os valores efetivos (sem segredos) no manifesto da execução.

## Dependências

- SPEC-0026 (fluxo e conexões), SPEC-0019 (coleção por Base), SPEC-0001 (política de sincronização). Ordem: BACKLOG-0035 (apagar Base) vem antes por ser defeito.

## Situações de erro

- Valor fora do limite ou tipo errado: erro em linha, sem avançar.
- `sync_mode` não suportado pelo provider: recusado pelo backend com mensagem clara.
- Prévia indisponível: mensagem existente do fluxo, sem perder as escolhas.

## Escopo

- Dentro: as seis estratégias de divisão confirmadas para Markdown, com os campos de cada uma; expor os grupos confirmados na Pergunta 1 nas etapas Divisão e Publicação; guardar por Base; refletir na Prévia; compatibilidade com Bases anteriores; teste real pelo front.
- Dentro também: ações no topo da Prévia, seletor de chunks por página, correção do contraste dos seletores e cadastro de conexão em painel lateral na Publicação.
- Fora: rascunho e retomada do fluxo (backlog próprio); validação (`limiar_minimo`, `top_k`), log e caminhos do servidor; tela global de configurações; editar a configuração de uma Base existente; outros providers e formatos; quinta etapa no fluxo.

## Dúvidas, decisões e riscos

- **Decisão (Pergunta 1, 2026-10-08):** entram divisão (`generate_section_summaries`, `section_summary_min_children`, `headers_to_split_on`), qualidade e contrato (`qualidade.minimo_util`, `contrato_markdown.status_bloqueado`) e embedding e vector store (`embedding.batch_size`, `vector_store.sync_mode`, `namespace`, `index_name`). Ficam fora validação (`limiar_minimo`, `top_k`), log e caminhos. Resposta original: `1`.
- **Decisão (Pergunta 2, 2026-10-08):** configurações guardadas por Base e escolhidas no fluxo de Nova Base; o `config.yaml` vira só o padrão inicial; Bases antigas mantêm o comportamento. Resposta original: `1`.
- **Decisão (Pergunta 3, 2026-10-08):** campos distribuídos nas etapas existentes: resumos de seção e headers na Divisão; bloco Qualidade (mínimo útil e status bloqueados) na Divisão; `batch_size`, `sync_mode`, `namespace` e `index_name` na Publicação; campos pouco usados em bloco Avançado recolhido; o fluxo segue com quatro etapas. Resposta original: `1`.
- **Decisão (Pergunta 4, 2026-10-08):** `sync_mode` visível e editável na Publicação, padrão `mirror`, com aviso da consequência; o backend valida pela política de segurança existente (`SyncSafetyPolicy`, SPEC-0001). Resposta original: `1`.
- **Decisão (2026-10-08, rodada adicional pedida pela pessoa):** pedido original: "eu quero todas as opções que o langchain/langgraph v1+ tem disponível, por ser a base de todo o projeto". Resposta: opção 1. Entram na etapa Divisão as estratégias de `langchain-text-splitters` aplicáveis a Markdown sem dependência nova: `MarkdownHeaderTextSplitter`, `MarkdownTextSplitter`, `ExperimentalMarkdownSyntaxTextSplitter`, `RecursiveCharacterTextSplitter`, `CharacterTextSplitter` e `TokenTextSplitter`. Cada estratégia mostra só os campos que usa, e a Prévia reflete a escolha. Ficam fora: splitters de sentenças/NLP (NLTK, spaCy, Sentence Transformers), `SemanticChunker` (`langchain_experimental`), splitters de outros formatos (HTML, LaTeX, Python, JS, JSON) e `KonlpyTextSplitter`.
- **Evidência:** a versão instalada de `langchain-text-splitters` expõe os seis splitters escolhidos; `TokenTextSplitter` depende de `tiktoken`, e a spec deve confirmar que ele já está no lock antes de expô-lo.
- **Decisão (2026-10-08):** pedido original: "quando estiver na previsa o botçao de seguir deve ficar na parte de cima e não no final da previa para não ter que rolar a pagina até o final" e "na previa quando haver muitos chunks tem a opção de ler 10, depois 20, 50 75 e 100". Entram neste item: ações Voltar e Próxima no topo da etapa Prévia e seletor de chunks por página com 10, 20, 50, 75 e 100 (o backend já aceita até 100 por página).
- **Decisão (2026-10-08):** o defeito do dropdown no tema escuro (opções com texto e fundo da mesma cor nos `select` das etapas Divisão e Publicação) é corrigido neste item.
- **Decisão (2026-10-08):** cadastrar conexões de embeddings e Qdrant em painel lateral dentro da etapa Publicação, sem sair do fluxo e sem perder arquivos e configurações; a nova conexão já aparece selecionável. Origem: a pessoa concordou com a melhoria sugerida ("exatamente a melhoria possivel sugerida") e com a ordem de trabalho proposta.
- **Fora deste item (decisão de 2026-10-08):** rascunho e retomada do fluxo de Nova Base vão para backlog próprio, com descoberta de dados.
- **Suposição recomendada, a confirmar na spec:** a barra de ações da Prévia fica fixa no topo ao rolar.
- **Suposição (não confirmada, herdada da SPEC-0026):** só owner/admin usam o fluxo; o frontmatter por arquivo continua prevalecendo sobre o formulário; os limites e padrões vêm de `GET /api/v1/ingestao/padroes`.
- **Risco:** `mirror` remove chunks ausentes na origem; `namespace` e `index_name` têm efeito que depende do provider (a spec deve confirmar no código antes de expô-los).
- **Evidência:** modelo e dimensões do embedding já são definidos na conexão (SPEC-0026).

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promover com `$specsfy-03-specify` depois do BACKLOG-0035.
