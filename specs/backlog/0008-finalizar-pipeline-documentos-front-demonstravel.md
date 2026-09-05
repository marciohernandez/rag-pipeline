# Backlog: Finalizar pipeline de documentos e criar front demonstrável

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0008 |
| Status | Ready for specification |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Pipeline de documentos demonstrável de ponta a ponta |
| Tipo | Épico |
| Prioridade | Não priorizado |
| Milestones | M01 |
| Criado em | 2026-09-01 |
| Spec promovida | Nenhuma |

## Ideia original

quero finalizar e deixar funcional a instesteam de documentos, o que é a parte 2 do projeto. depois que estiver funcional quero trabalhar no front proque preciso apresentar para equipe, mesmo que não esteja tudo funcionado mas apresentar essa parte funcional com front.

## Problema percebido

O pipeline deste componente ainda precisa ser concluído e comprovado no fluxo de Markdown para chunks, embeddings, indexação vetorial e validação da recuperação antes de poder ser demonstrado à equipe.

## Pessoa afetada ou beneficiada

Marcio, como operador do pipeline, e a equipe de consultoria que acompanhará a demonstração.

## Resultado ou valor esperado

Executar e demonstrar uma fatia funcional do pipeline por meio de um front, mesmo que outras partes do produto permaneçam incompletas.

## Contexto

A parte 2 corresponde ao pipeline existente neste repositório: receber Markdown, gerar chunks e embeddings, indexar no banco vetorial e validar a recuperação. A ingestão multiformato da Fase 1 não faz parte desta definição. A ordem declarada é concluir primeiro o pipeline e depois preparar o front para apresentação.

## Referências relacionadas

- `specs/inbox/2026-08-31-220507-finalizar-ingestao-de-documentos-e-preparar-front-para-apresentacao.md`: captura de origem, preservada integralmente.
- `specs/backlog/0002-compatibilizar-contrato-markdown.md`: backlog relacionado ao contrato dos documentos Markdown recebidos pelo pipeline.
- `specs/backlog/0006-validar-recuperacao-operacao.md`: backlog relacionado e dependência para comprovar a recuperação de ponta a ponta.
- `specs/backlog/0007-gates-entrega-handoff.md`: backlog relacionado aos gates que encerram o componente e preparam sua integração.
- `PROJECT.md`: delimita este componente ao fluxo de Markdown, chunks, embeddings, indexação e recuperação, sem ingestão multiformato.
- `docs/flows.md` e `docs/application.md`: documentação do fluxo CLI e das superfícies implementadas atualmente.
- `docs/frontend.md` e `INTERFACE.md`: confirmam que ainda não existe frontend neste repositório.
- `.specsfy/DATABASE.md`, seção `Informações a guardar confirmadas`: registra base de documentos, execução do pipeline e consulta de validação, com formatos, vínculos, acesso e ciclo de vida confirmados.

## Comportamento esperado

1. Marcio seleciona uma base Markdown representativa e inicia o pipeline.
2. O pipeline carrega os documentos, gera chunks rastreáveis e produz o manifesto de auditoria.
3. Os chunks recebem embeddings e são indexados no banco vetorial configurado.
4. Consultas de validação recuperam resultados esperados da base indexada.
5. A mesma base pode ser processada novamente sem criar pontos duplicados.
6. No frontend do `rag-pipeline`, Marcio seleciona ou envia uma base Markdown, inicia o processamento, acompanha as etapas e contagens, executa uma consulta e visualiza o resultado com os chunks-fontes recuperados.
7. A demonstração permite enviar vários arquivos `.md` para o projeto ativo e oferece uma base Markdown preparada como contingência.

## Regras de negócio

- O frontend não executa scripts nem acessa o banco vetorial diretamente; toda operação passa pelo backend FastAPI de `src/app/`.
- Depois da consolidação, o pipeline expõe uma interface Python estável como módulo interno do backend, sem exigir um microserviço separado.
- O processamento ocorre como tarefa assíncrona; o frontend acompanha o estado e as contagens sem manter uma requisição HTTP bloqueada até o fim.
- A CLI atual pode continuar como adaptador operacional, mas não será o contrato usado pelo frontend.
- Cada upload e cada execução pertencem ao projeto ativo no contexto do tenant; a base preparada para demonstração também deve ser associada explicitamente a esse contexto.
- Cada envio aceita somente arquivos `.md` em UTF-8, com no máximo 50 arquivos, 5 MB por arquivo e 50 MB no total.
- Formato, codificação e tamanho são validados antes de agendar a execução; um envio inválido não inicia processamento parcial.
- A primeira demonstração exige uma conta `owner` interna preparada para Marcio. O backend aplica tenant, projeto e permissões desde essa fatia.
- Cadastro, convite e administração completa de usuários e papéis não pertencem a esta entrega.

## Critérios de aceitação

```gherkin
Scenario: Executar o pipeline completo com uma base Markdown representativa
  Given uma base Markdown válida e um banco vetorial configurado
  When Marcio executa o pipeline completo
  Then os chunks e o manifesto de auditoria são gerados
  And os vetores são indexados no banco configurado
  And as consultas de validação recuperam os resultados esperados

Scenario: Repetir o processamento sem duplicar dados
  Given uma base Markdown que já foi processada e indexada com sucesso
  When Marcio executa novamente o mesmo pipeline sem alterar a base
  Then nenhum ponto duplicado é criado no banco vetorial
  And o resultado continua recuperável pelas consultas de validação

Scenario: Demonstrar o pipeline pelo frontend
  Given uma base Markdown disponível para processamento
  When Marcio inicia a execução pelo frontend
  Then ele acompanha as etapas e contagens do processamento
  And pode realizar uma consulta na base indexada
  And visualiza o resultado e os chunks-fontes recuperados

Scenario: Acompanhar uma execução assíncrona
  Given uma base Markdown aceita pelo backend de aplicação
  When Marcio inicia seu processamento no frontend
  Then o FastAPI agenda a execução por meio da interface interna do pipeline
  And o frontend pode consultar seu estado e suas contagens até a conclusão
  And nenhuma CLI ou banco vetorial é acessado diretamente pelo navegador

Scenario: Usar upload real ou base de contingência
  Given Marcio está no contexto de um projeto ativo
  When ele prepara uma nova demonstração
  Then pode enviar vários arquivos Markdown para esse projeto
  And pode escolher uma base Markdown preparada quando precisar da contingência
  And a origem escolhida fica identificada na execução

Scenario: Repetir uma execução que falhou
  Given uma execução que falhou em uma etapa do pipeline
  When owner ou admin consulta a tentativa no frontend
  Then visualiza a etapa alcançada e uma mensagem de erro sem segredos
  And pode repetir toda a execução usando a mesma base
  And a nova tentativa não cria pontos duplicados

Scenario: Rejeitar um envio fora dos limites
  Given um envio com mais de 50 arquivos, arquivo maior que 5 MB, total maior que 50 MB, extensão diferente de `.md` ou conteúdo que não seja UTF-8
  When Marcio tenta iniciar o processamento
  Then o frontend identifica cada problema antes de agendar a execução
  And preserva os arquivos válidos para correção do envio
  And nenhum processamento parcial é iniciado
```

## Jornada e interface da demonstração

- Local: frontend deste repositório `rag-pipeline`.
- Ator inicial: Marcio, como operador interno.
- Início: enviar vários arquivos `.md` para o projeto ativo ou selecionar uma base Markdown preparada e iniciar seu processamento.
- Acompanhamento: exibir etapas e contagens suficientes para observar o progresso e o resultado.
- Validação: permitir uma consulta sobre a base indexada.
- Resultado: apresentar o conteúdo recuperado e os chunks-fontes que sustentam a recuperação.
- Stack planejada do frontend: Next.js App Router, shadcn/ui, Tailwind CSS e TanStack Query; ainda não implementada.
- Organização confirmada: duas telas principais.
  1. **Projeto**: lista bases e execuções e oferece upload ou seleção da base preparada.
  2. **Detalhe da execução**: mostra progresso, etapas, contagens, erros, repetição e a área de consulta com chunks-fontes.
- Navegação: toda tela usa o shell da aplicação e `Breadcrumb` com equipe ativa, projeto e tela atual. A linha de uma base ou execução abre o respectivo detalhe por mouse e teclado.
- Direção visual: aplicar os defaults de `DESIGNSYSTEM.MD`, sem exceção visual confirmada para esta entrega.
- **Tela Projeto**:
  - `PageHeader` compartilhado com nome do projeto, descrição, ação de enviar base e ação secundária de usar a base preparada;
  - ReUI `File Upload` em `Sheet` ou `Dialog` contextual, com múltiplos `.md`, validação, remoção antes do envio e preservação após erro;
  - ReUI `Data Grid` em largura total para bases e execuções, com `ID`, origem, status, documentos, chunks, última execução e atualização;
  - linha inteira abre o detalhe por mouse e teclado; ações internas de repetir e apagar não propagam a navegação;
  - `Badge`, `Alert`, filtros e estado vazio contextualizam status, falha e ausência de bases.
- **Tela Detalhe da execução**:
  - o mesmo `PageHeader`, configurado com status, retorno ao projeto e ação de repetir quando permitida;
  - indicadores curtos para documentos, chunks previstos, inseridos, mantidos e removidos, sempre com origem e atualização;
  - ReUI `Timeline` ou composição equivalente para etapas, horários e erro seguro;
  - formulário de consulta com label visível, envio, loading e preservação da pergunta após falha;
  - resultado seguido dos chunks-fontes, com identificação do documento e trecho recuperado;
  - ação destrutiva de apagar disponível somente para `owner` e `admin`, com confirmação da consequência.
- Estados obrigatórios nas duas telas: loading, vazio, processando, sucesso, falha, conteúdo parcial, sem permissão e indisponibilidade de integração.
- Acessibilidade: ordem de foco coerente, foco visível, retorno de foco após overlays, operação por teclado, mensagens associadas aos controles, status anunciado e chunks-fontes não comunicados apenas por cor.
- Responsividade: desktop prioriza comparação e investigação; mobile preserva equipe, projeto, status, ação principal e consulta, refluindo o conteúdo sem esconder a recuperação de erro.
- Autenticação inicial: Marcio acessa com uma conta `owner` interna preparada; as telas respeitam tenant, projeto e permissões, sem incluir administração de usuários.
- Limites confirmados: até 50 arquivos `.md` UTF-8, 5 MB por arquivo e 50 MB por envio, validados antes do processamento.

## Qualidades e operação

- Segurança: cada arquivo, execução e consulta é isolado pelo tenant e projeto ativo. `owner` e `admin` administram bases e execuções; `member` acompanha e consulta, sem apagar.
- Privacidade: apagar uma base exige confirmação e remove arquivos, execuções, consultas, chunks e vetores associados; permanece somente um registro de exclusão sem o conteúdo removido.
- Desempenho e volume: o processamento não bloqueia a requisição HTTP; cada envio aceita até 50 arquivos Markdown UTF-8, 5 MB por arquivo e 50 MB no total.
- Auditoria e observabilidade: o frontend consome o estado e as contagens estruturadas da execução; o formato e a persistência ainda precisam ser definidos.

## Dependências

- BACKLOG-0002: preservar o contrato dos documentos Markdown durante o processamento.
- BACKLOG-0006: fornecer a validação repetível da recuperação e das contagens operacionais.
- BACKLOG-0007: consolidar os gates de qualidade e entrega depois que a fatia funcional estiver comprovada. Concluído na SPEC-0007.
- BACKLOG-0011: define a fronteira interna entre pipeline e backend de aplicação, a fachada de casos de uso e as duas dívidas bloqueantes. É pré-requisito direto da fatia 2.
- Backend de aplicação: FastAPI para o contrato HTTP e execução assíncrona, implementado em `src/app/` neste repositório.
- Frontend: implementado neste repositório, consumindo o backend de aplicação.

## Decomposição confirmada do épico

1. **Finalizar e comprovar o componente atual**
   - Repositório responsável: este repositório, então chamado `rag-ingestion-pipeline`.
   - Escopo: executar os backlogs 0001 a 0007 até comprovar o fluxo Markdown → chunks → embeddings → indexação → recuperação idempotente.
   - Saída: componente estável, testado, documentado e pronto para migração.
2. **Incorporar o componente ao backend de aplicação**
   - Repositório responsável: este repositório, `rag-pipeline`.
   - Escopo: criar a fronteira interna entre pipeline e aplicação, a interface Python estável, o contrato FastAPI, a tarefa assíncrona e a persistência.
   - Saída: backend integrado capaz de receber uma base, iniciar o pipeline e fornecer estado, contagens, erros e consulta.
   - Pré-requisito: BACKLOG-0011, que define a fronteira, a fachada e as dívidas bloqueantes.
3. **Entregar o frontend demonstrável**
   - Repositório responsável: este repositório, `rag-pipeline`.
   - Escopo: implementar a tela do projeto e o detalhe da execução, incluindo upload/base preparada, progresso, repetição, exclusão e consulta com chunks-fontes.
   - Saída: jornada ponta a ponta apresentável à equipe.

As fatias são sequenciais e todas acontecem neste repositório.

**Atualização de 2026-09-03 — premissa superada.** Este épico foi escrito
quando `rag-ingestion-pipeline` e `rag-pipeline` eram dois repositórios
distintos, e declarava que as fatias 2 e 3 pertenciam a um repositório irmão.
Os commits `e2d8b1b` e `0fe7b1b` consolidaram ambos em um único repositório.
A decomposição acima foi corrigida para a realidade de repositório único; as
decisões originais ficam preservadas em `Dúvidas, decisões e riscos` como
proveniência, marcadas como superadas.

## Situações de erro

- Upload inválido, falha no processamento, indisponibilidade do provider de embeddings ou do banco vetorial e falha na consulta precisam aparecer no frontend sem expor credenciais.
- Uma falha preserva a tentativa, a etapa alcançada e o erro seguro no histórico.
- `Owner` ou `admin` pode repetir toda a execução com a mesma base; a repetição é idempotente e não cria pontos duplicados.
- A primeira entrega não retoma automaticamente da etapa interrompida.

## Escopo

- Dentro: receber documentos Markdown; gerar chunks e embeddings; indexar no banco vetorial; validar a recuperação; definir a fronteira interna e o contrato consumível pelo backend; implementar o backend de aplicação; preparar o front que demonstre a fatia funcional à equipe. Tudo neste repositório.
- Fora: cadastro, convite e administração completa de usuários; ingestão de PDF, DOCX ou outros formatos; curadoria cruzada; detecção de contradições; funcionalidades ainda incompletas que não forem necessárias para a demonstração desta fatia.

## Dúvidas, decisões e riscos

- Decisão confirmada na Pergunta 1: a expressão original `instesteam de documentos` refere-se ao pipeline deste componente, no fluxo Markdown → chunks → embeddings → indexação vetorial → validação da recuperação.
- Decisão confirmada: a ingestão multiformato do projeto-mãe não pertence a esta parte 2.
- Decisão confirmada na segunda rodada: o pipeline precisa comprovar o fluxo completo com uma base Markdown representativa, incluindo chunks, manifesto, indexação, recuperação esperada e reexecução sem duplicidade.
- Decisão confirmada na terceira rodada, **superada em 2026-09-03**: o frontend da apresentação pertencia ao projeto-mãe `rag-pipeline`, então um repositório separado. Com a consolidação, o frontend pertence a este mesmo repositório.
- Análise arquitetural: o projeto-mãe já existe em repositório próprio, com constituição 1.2.1, briefing, stack FastAPI/Next.js e apenas dois commits. Este componente possui histórico, specs e runtime próprios. Substituir um pelo outro agora confundiria as fontes normativas; uma consolidação posterior no projeto-mãe pode preservar os dois históricos.
- Decisão confirmada na quarta rodada, **cumprida em 2026-09-03**: adotar consolidação gradual. A consolidação foi executada pelos commits `e2d8b1b` e `0fe7b1b`: este repositório passou a ser o `rag-pipeline` e reúne as duas fases. Não há mais repositório a arquivar.
- Restrição de transição, **cumprida**: o histórico foi preservado na consolidação.
- Decisão confirmada em 2026-09-03, durante o refinamento do BACKLOG-0011: a fatia 2 depende da fronteira interna definida naquele item, e ele declara duas dívidas bloqueantes que precisam ser resolvidas antes de `src/app/` receber implementação.
- Decisão confirmada na quinta rodada: a jornada mínima da demonstração cobre entrada de uma base Markdown, início e acompanhamento do processamento, consulta e exibição do resultado com chunks-fontes.
- Decisão confirmada na sexta rodada: depois da consolidação, o pipeline será um módulo interno do backend do `rag-pipeline`, chamado por uma interface Python estável; o FastAPI agenda a execução assíncrona e expõe status, contagens e consulta ao frontend.
- Decisão confirmada na sétima rodada: a entrada da demonstração aceita upload de vários arquivos `.md` no projeto ativo e também uma base preparada como contingência, mantendo a origem identificada.
- Decisão confirmada em `$specsfy-data-discovery`: manter histórico auditável das bases, execuções, etapas, contagens, erros, manifesto, consultas e chunks-fontes enquanto o projeto existir.
- Decisão confirmada em `$specsfy-data-discovery`: `owner` e `admin` podem enviar, processar, repetir, administrar e apagar; `member` pode acompanhar e consultar, sem apagar.
- Decisão confirmada em `$specsfy-data-discovery`: quando `owner` ou `admin` apaga uma base, o sistema remove seu conteúdo, execuções, consultas, chunks e vetores, preservando somente um registro sem conteúdo de que a exclusão ocorreu.
- Decisão confirmada na oitava rodada: uma falha preserva a tentativa, mostra etapa e erro seguro e permite a `owner` ou `admin` repetir toda a execução com a mesma base; a primeira entrega não retoma da etapa interrompida.
- Decisão confirmada na nona rodada: organizar a demonstração em duas telas principais — projeto e detalhe da execução — mantendo upload/base de exemplo na primeira e progresso/consulta na segunda.
- Decisão confirmada na décima rodada: a demonstração usa uma conta `owner` interna preparada para Marcio; tenant, projeto e permissões são aplicados pelo backend, enquanto gestão completa de usuários fica fora da fatia.
- Decisão confirmada na décima primeira rodada: cada envio aceita até 50 arquivos `.md` UTF-8, 5 MB por arquivo e 50 MB no total; entradas inválidas são rejeitadas antes de agendar a execução.
- Decisão confirmada na décima segunda rodada: decompor o épico em três fatias sequenciais — estabilização do componente atual, incorporação ao backend do projeto-mãe e frontend demonstrável.
- Nenhuma lacuna aplicável permanece no nível deste épico. Cada fatia detalhará suas decisões locais na raiz responsável.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** concluir o pipeline de documentos e torná-lo demonstrável de ponta a ponta neste repositório.
2. **Atores:** Marcio como `owner`; `admin` administra bases e execuções; `member` acompanha e consulta sem apagar.
3. **Escopo:** estabilização do pipeline, incorporação ao backend de aplicação em `src/app/` e duas telas demonstráveis no frontend — tudo neste repositório.
4. **Fora de escopo:** ingestão multiformato, curadoria, contradições e gestão completa de usuários.
5. **Jornada essencial:** enviar ou escolher base Markdown, acompanhar processamento, validar recuperação, consultar chunks-fontes, repetir falha e apagar quando autorizado.
6. **Aceite:** cenários Given/When/Then desta entrada cobrem execução completa, idempotência, interface, tarefa assíncrona, contingência, falha e limites do upload.
7. **Restrições:** histórico preservado na consolidação já executada, fronteira interna definida pelo BACKLOG-0011, isolamento por tenant/projeto e nenhum segredo exposto.
8. **Suposições confirmadas:** frontend e backend neste repositório, FastAPI em `src/app/` chamando a fachada de `src/pipeline/` e conta `owner` preparada para a demonstração.
9. **Decisões abertas:** nenhuma no nível do épico; detalhes locais pertencem à especificação de cada fatia.

## Próximo passo

**Atualizado em 2026-09-05.** Os backlogs 0001 a 0007 foram concluídos nas
SPEC-0001 a SPEC-0007, encerrando a fatia 1. O BACKLOG-0011 (fronteira interna
e dívidas bloqueantes) e o BACKLOG-0015 (incorporação ao backend de aplicação)
foram concluídos e promovidos à SPEC-0012 (`Complete`), encerrando a fatia 2.

O próximo passo é a fatia 3: o frontend demonstrável descrito na seção
"Jornada e interface da demonstração" acima. Como este item de backlog ainda
mistura as três fatias, refinar com `$specsfy-02-backlog` para isolar o escopo
da fatia 3 antes de promover com `$specsfy-03-specify`.
