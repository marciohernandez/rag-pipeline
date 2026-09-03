# Backlog: Criar gate automatizado de qualidade de chunks e metadados

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0005 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Qualidade da preparação RAG |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-08-31 |
| Refinado em | 2026-09-03 |
| Spec promovida | `specs/draft/0006-gate-qualidade-chunks-metadados/spec.md` |

## Ideia original

Validar automaticamente tamanho, conteúdo, identidade e metadados dos chunks antes de qualquer indexação remota, gerando diagnóstico objetivo.

## Problema percebido

A auditoria encontrou chunks muito curtos e muito longos, mas o pipeline não possui um gate automatizado que impeça ou sinalize saídas inadequadas.

O refinamento de 2026-09-03 mediu a base indexada e reposicionou o problema. A
métrica de tamanho que originou o item é, em boa parte, ruído: os chunks curtos
são majoritariamente unidades semânticas completas e não existe chunk gigante.
O dano real está em defeitos que nenhuma regra de tamanho detecta — perda de
estrutura de headings na origem, truncamento de frase no corte por tamanho,
duplicata exata de conteúdo e texto colapsado por tabulação.

## Pessoa afetada ou beneficiada

Operadores que preparam bases RAG e mantenedores que ajustam regras de chunking.

## Resultado ou valor esperado

Cada execução comprova a qualidade mínima dos chunks e bloqueia indexação quando invariantes críticos falham.

Os sinais que não bloqueiam ficam legíveis por documento, apontando qual arquivo
de origem revisar em vez de listar chunks isolados.

## Contexto

Item P1 do milestone M01. A auditoria local observou 65 chunks abaixo de 250
caracteres e 12 acima de 1000 em 208 chunks.

### Medição de 2026-09-03 sobre `output/vivo_gold_banda_larga_pf/chunks.json`

Base: 208 chunks (191 `detail`, 17 `section_summary`), sete documentos.

| Medida | `detail` | `section_summary` |
| --- | --- | --- |
| n | 191 | 17 |
| mínimo | 99 | 117 |
| mediana | 398 | 219 |
| p90 | 950 | 386 |
| máximo | 1046 | 415 |

Confirmações e refutações:

- Os números do backlog original se confirmam: 65 chunks abaixo de 250 e 12
  acima de 1000.
- O teto está sendo respeitado: o máximo de 1046 é o `chunk_size` de 1000 mais
  o breadcrumb injetado. Nenhum chunk passa de 1200.
- Os menores chunks são legítimos. O menor da base, com 99 caracteres, é
  `[Aplicativos e Conteúdos Incluídos > Música > Apple Music] ### Apple Music —
  30 dias grátis.`, uma unidade semântica completa.
- `secao` vazia em 50 chunks e `subsecao` em 93 não é falha uniforme de
  metadado: concentra-se em dois documentos.

### Defeitos reais encontrados

| Sinal | Ocorrências |
| --- | --- |
| Perda de estrutura de headings | 2 de 7 documentos, com 94% e 73% dos chunks sem `secao` |
| Truncamento no meio da frase | 14 de 191 chunks `detail` |
| Duplicata exata no mesmo caminho lógico | 1 grupo, 2 chunks |
| Texto colapsado por tabulação | 5 chunks, todos de um documento |
| Conteúdo útil abaixo de 60 caracteres | 8 chunks |

Perda de estrutura por documento:

| Documento | chunks | sem `secao` | sem `subsecao` |
| --- | --- | --- | --- |
| `regulamento_regras_das_categorias_de_clientes_vivo_beneficios_v6_20241213.md` | 39 | 37 (94%) | 39 (100%) |
| `regulamento-cinemark-vivo-valoriza-2025.md` | 15 | 11 (73%) | 15 (100%) |
| `Complemento Consolidado da Oferta Vivo Fibra.md` | 26 | 2 (7%) | 15 (57%) |
| `Benefícios Banda Larga PF.md` | 43 | 0 | 9 (20%) |
| `Oferta Vivo Fibra com SVA.md` | 59 | 0 | 7 (11%) |
| `Termos e condições da assinatura.md` | 13 | 0 | 6 (46%) |
| `vivo_fibra_pf_julho_2026.md` | 13 | 0 | 2 (15%) |

Causa raiz da perda de estrutura: o documento de regulamento escreve heading
dentro de bullet — `* ## **Ganhe R$50 em Vale Bonus**` — em 37 lugares. O
`MarkdownHeaderTextSplitter` não reconhece essa forma, então os 37 títulos ficam
invisíveis e todos os chunks do arquivo colapsam sob o mesmo breadcrumb
`[**BENEFÍCIOS POR CATEGORIA**]`. Sem a estrutura, a frase de rodapé que a
origem repete a cada benefício produziu dois chunks byte a byte idênticos. O
mesmo arquivo tem cinco linhas separadas por tabulação, que o processamento
colapsa em `SaibamaissobreestebenefícioconsultandoseuRegulamento`.

### A base atual não está falhando

A validação de 2026-09-02 (`output/vivo_gold_banda_larga_pf/validation-1ff74dbb-d597-43b2-9ec6-73079e78989c.json`)
registra `desfecho: aprovado`, 208 chunks previstos e 208 observados, com as dez
consultas do gabarito aprovadas. As duas consultas que caem dentro dos documentos
com estrutura perdida passam: `Quanto de Vale Bônus o cliente Vivo Fibra pode
receber por mês?` com score 0,779 e `Quantos ingressos com 50% de desconto no
Cinemark o cliente Gold tem por mês?` com 0,754.

Os defeitos são risco latente de qualidade, não falha presente de recuperação.
Essa evidência é o motivo de a duplicata exata ter sido classificada como sinal
e não como bloqueio.

## Referências relacionadas

- `src/chunker.py`, `src/identity.py` e `src/manifest.py`: geração, identidade e rastreabilidade atuais. Tipo: código-fonte da área afetada.
- `config.yaml`, seção `chunking`: limites configurados. Tipo: configuração afetada.
- `PLANO_CHUNKS_RESUMO_QDRANT.md`: requisitos históricos de qualidade e sincronização. Tipo: documentação relacionada.
- `specs/backlog/0002-compatibilizar-contrato-markdown.md`, linha 65: aponta este item como responsável por validar a qualidade dos chunks. Tipo: backlog relacionado.
- `specs/backlog/0007-gates-entrega-handoff.md`, linha 73: declara este gate como dependência do fechamento do M01. Tipo: backlog relacionado.
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: épico que contém esta fatia. Tipo: backlog relacionado.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md`: estabeleceu `src/manifest.py` como ponto de bloqueio pré-indexação e a cultura fail-closed. Tipo: spec relacionada.
- `specs/completed/0004-validar-recuperacao-operacao/spec.md`: estabeleceu o padrão de CLI de diagnóstico com relatório legível, JSON estruturado e códigos de saída 0/1/2, reaproveitado aqui. Tipo: spec relacionada.
- `.specsfy/RULES.md`: configuração centralizada, ausência de identidade de cliente no código e registro de contagens por execução. Tipo: documentação relacionada.
- `specs/inbox/2026-09-03-072811-reanalisar-a-quebra-de-chunks-e-onde-o-resumo-deve-viver.md`:
  captura que pede reanálise da estratégia de quebra e decisão sobre o resumo
  viver como metadado em vez de chunk isolado. Tipo: backlog relacionado ainda
  não promovido. Não é duplicata: aquela captura quer mudar a quebra, esta fatia
  quer medi-la sem alterá-la.
- Linear `LEAD-90`: tracking do item no milestone. Tipo: projeção de acompanhamento.

## Comportamento esperado

1. O operador executa o pipeline sobre uma base Markdown.
2. Depois de gerar os chunks e antes de qualquer escrita no vector store, o gate
   avalia o conjunto local.
3. Quando um invariante crítico falha, o gate impede a indexação, identifica a
   falha e encerra sem escrever no destino.
4. Quando nenhum invariante crítico falha, a indexação prossegue e o gate
   publica o relatório de sinais de qualidade.
5. O operador pode executar o gate isoladamente, como comando de diagnóstico,
   sobre os chunks já gerados, sem indexar.
6. O relatório apresenta os sinais agrupados por documento de origem, indicando
   quais arquivos revisar.
7. O resultado estruturado fica gravado em arquivo próprio da execução, com o
   detalhe por chunk.

## Regras de negócio

### Níveis

- O gate tem dois níveis. Invariantes críticos **bloqueiam** a indexação. Sinais
  de qualidade **relatam** e não bloqueiam.
- Somente regras determinísticas, sem heurística, podem bloquear.

### Nível crítico — bloqueia

- Nenhum chunk gerado.
- Chunk sem `chunk_id`.
- `chunk_id` duplicado no conjunto.
- Contagem do manifesto inconsistente com o número de chunks.
- Chunk com conteúdo vazio ou composto apenas pelo breadcrumb.
- Chunk sem algum metadado de rastreabilidade obrigatório: `document_id`,
  `source_hash`, `project_id`, `chunk_hash` e `chunk_type`.

### Nível de sinal — relata

- Perda de estrutura: proporção de chunks sem `secao` e sem `subsecao`, por
  documento.
- Truncamento no meio da frase.
- Duplicata exata de conteúdo no mesmo caminho lógico.
- Texto colapsado por tabulação.
- Distribuição de tamanho, quebrada por `chunk_type`.
- Conteúdo útil abaixo do mínimo configurado.

### Limiares

- O **máximo** de tamanho é derivado do `chunk_size` efetivo de cada documento,
  somada a margem do breadcrumb injetado. Não é um número fixo global, porque
  `src/chunker.py` permite que o frontmatter sobrescreva `chunk_size` por
  documento via `chunk_size_recommended`.
- O **mínimo** é configurado explicitamente em `config.yaml`, com valor único
  por base, e é medido sobre o **conteúdo útil**, descontado o breadcrumb
  repetido no `page_content`. Padrão inicial: 60 caracteres.
- Nenhum limiar carrega identidade, produto ou domínio de cliente, conforme
  `.specsfy/RULES.md`.

### Execução e artefatos

- O gate roda embutido no `pipeline.py`, entre a geração dos chunks e a
  indexação, e também é exposto como comando próprio de diagnóstico.
- O comando de diagnóstico produz relatório legível no stdout e resultado
  estruturado em `output/<base>/quality-<uuid>.json`.
- O `manifest.json` mantém sua responsabilidade única de identidade e contagens;
  o resultado do gate não é gravado dentro dele.
- Esta fatia não acumula histórico entre execuções.

## Critérios de aceitação

```gherkin
Scenario: Bloquear a indexação quando um invariante crítico falha
  Given um conjunto de chunks em que um chunk está sem chunk_id
  When o operador executa o pipeline completo
  Then o gate impede a indexação antes de qualquer escrita no vector store
  And o motivo do bloqueio identifica o invariante violado
  And nenhum ponto é escrito no destino

Scenario: Prosseguir com a indexação quando só há sinais de qualidade
  Given um conjunto de chunks íntegro, com 14 chunks truncados no meio da frase
  When o operador executa o pipeline completo
  Then a indexação prossegue normalmente
  And o relatório registra o truncamento como sinal, sem bloquear

Scenario: Apontar o documento de origem responsável pela perda de estrutura
  Given uma base em que dois documentos concentram os chunks sem secao
  When o gate publica o relatório
  Then os sinais aparecem agrupados por documento de origem
  And os dois documentos afetados aparecem com sua proporção de chunks sem secao
  And os documentos saudáveis não são apontados como defeituosos

Scenario: Medir o mínimo sobre o conteúdo útil, não sobre o bruto
  Given um chunk cujo page_content tem 99 caracteres, dos quais 59 são breadcrumb
  When o gate avalia o tamanho mínimo com o padrão de 60 caracteres
  Then o chunk é sinalizado pelo conteúdo útil de 40 caracteres
  And o comprimento bruto de 99 caracteres não é usado nessa decisão

Scenario: Derivar o máximo do chunk_size efetivo do documento
  Given um documento cujo frontmatter declara chunk_size_recommended de 2000
  When o gate avalia o tamanho máximo dos chunks desse documento
  Then o limite aplicado deriva de 2000 mais a margem do breadcrumb
  And nenhum chunk desse documento é sinalizado por ultrapassar o padrão global

Scenario: Relatar duplicata exata sem bloquear
  Given dois chunks com conteúdo idêntico e chunk_ids distintos no mesmo caminho lógico
  When o operador executa o pipeline completo
  Then a indexação prossegue
  And o relatório registra a duplicata como sinal, identificando o documento

Scenario: Executar o gate isoladamente como diagnóstico
  Given um arquivo de chunks já gerado
  When o operador executa o comando de diagnóstico sobre esse arquivo
  Then o relatório legível é apresentado
  And o resultado estruturado é gravado em output/<base>/quality-<uuid>.json
  And nada é escrito no vector store

Scenario: Gravar o resultado sem alterar o manifesto
  Given uma execução em que o gate publicou seu relatório
  When o operador inspeciona os artefatos da execução
  Then o resultado do gate está em seu arquivo próprio
  And o manifest.json preserva somente identidade e contagens
```

## Qualidades e operação

- **Segurança:** o gate é leitura pura sobre o conjunto local. Não escreve no
  vector store, não abre conexão remota e não executa comando destrutivo.
- **Privacidade:** relatório e resultado estruturado não registram credenciais,
  tokens nem URLs de destino, conforme `.specsfy/RULES.md`. Trechos de conteúdo
  citados no relatório limitam-se ao necessário para identificar o defeito.
- **Desempenho e volume:** a avaliação percorre o conjunto já em memória, sem
  chamada de rede e sem novo embedding. Referência atual: 208 chunks e sete
  documentos.
- **Auditoria e observabilidade:** cada execução registra o desfecho, o número
  de invariantes avaliados e a contagem de cada sinal, no padrão de registro por
  execução já adotado pelo componente.
- **Testes:** Red-Green-Refactor com Pest não se aplica; o projeto usa Pytest.
  As regras determinísticas exigem teste unitário próprio; os sinais exigem
  teste sobre um conjunto sintético com cada defeito representado.

## Dependências

- `src/manifest.py`, entregue pela SPEC-0001: ponto de bloqueio pré-indexação já
  existente, que este item estende em vez de substituir.
- SPEC-0004: padrão de CLI de diagnóstico, relatório legível, JSON estruturado e
  códigos de saída, reaproveitado por decisão da Pergunta 3.
- BACKLOG-0007: consome este gate como evidência de qualidade para encerrar o
  milestone M01.

## Situações de erro

- Arquivo de chunks ausente, ilegível ou malformado no comando de diagnóstico:
  o gate informa a impossibilidade de avaliar e não indexa.
- `config.yaml` sem o mínimo configurado: o gate aplica o padrão inicial de 60
  caracteres e registra que usou o padrão.
- Documento sem `chunk_size` efetivo determinável: o gate registra a
  impossibilidade de derivar o máximo daquele documento e segue avaliando os
  demais sinais.
- Falha ao gravar o resultado estruturado: o relatório legível é preservado no
  stdout e a falha de escrita é informada, sem mascarar o desfecho do gate.

## Escopo

- **Dentro:** avaliação determinística dos invariantes críticos antes da
  indexação; cálculo dos cinco sinais de qualidade; derivação do máximo por
  documento e mínimo configurável sobre conteúdo útil; bloqueio da indexação no
  `pipeline.py`; comando próprio de diagnóstico; relatório legível; resultado
  estruturado em arquivo próprio da execução; testes das regras e dos sinais.
- **Fora:** corrigir automaticamente os documentos de origem; deduplicar,
  reescrever ou rechunkar conteúdo; alterar a estratégia de chunking; histórico
  agregado ou comparação de qualidade entre execuções; veredito automático de
  severidade por arquivo; qualquer interface gráfica, que por decisão do
  BACKLOG-0008 pertence ao projeto-mãe `rag-pipeline`.

## Dúvidas, decisões e riscos

- **Decisão (Pergunta 1):** o gate tem dois níveis — invariantes críticos
  bloqueiam, sinais de qualidade relatam. Base: bloquear por tamanho reprovaria
  31% da base atual, cujos chunks curtos são majoritariamente legítimos.
- **Decisão (Pergunta 2):** somente regras determinísticas bloqueiam. Truncamento
  e texto colapsado são heurísticas e podem gerar falso positivo, então ficam no
  nível de sinal.
- **Decisão (Pergunta 3):** o gate roda embutido no `pipeline.py` e também como
  comando próprio de diagnóstico, com relatório legível e JSON estruturado.
- **Decisão (Pergunta 4):** máximo derivado do `chunk_size` efetivo de cada
  documento; mínimo explícito em `config.yaml`, único por base; relatório quebra
  os números por `chunk_type`.
- **Decisão (Pergunta 5):** duplicata exata de conteúdo é sinal, não bloqueio.
  Corrige a classificação inicial da Pergunta 2. Base: `chunk_id` duplicado
  quebraria a sincronização idempotente e é integridade; conteúdo duplicado com
  `chunk_id` distintos é ruído no top-k, e a validação de 2026-09-02 aprovou a
  base com esse defeito presente.
- **Decisão (Pergunta 6):** o relatório carrega os cinco sinais organizados por
  documento de origem, com o detalhe por chunk preservado no JSON estruturado.
  Base: o defeito se concentra em 2 dos 7 arquivos; o eixo documento é o que
  gera ação.
- **Decisão (Pergunta 7):** resultado gravado em `output/<base>/quality-<uuid>.json`,
  fora do `manifest.json`, sem histórico agregado nesta fatia.
- **Decisão (Pergunta 8):** mínimo medido sobre o conteúdo útil, descontado o
  breadcrumb, com padrão inicial de 60 caracteres. Base: sinaliza 8 chunks (4%)
  em vez dos 65 (31%) da métrica bruta original.
- **Inferência a confirmar na spec:** o gate também roda no modo `--only-chunks`,
  já que esse é o modo usado para ajustar o chunking sem indexar.
- **Inferência a confirmar na spec:** os códigos de saída do comando de
  diagnóstico seguem o padrão da SPEC-0004 — 0 aprovado, 1 reprovado, 2 não foi
  possível avaliar.
- **Risco:** o padrão inicial de 60 caracteres foi calibrado sobre uma única
  base. Outra base pode exigir ajuste, o que a configuração explícita permite.
- **Risco:** a detecção de truncamento é heurística e tende a falso positivo em
  listas, tabelas e headings. A medição já exclui esses casos, mas o critério
  precisa de teste sobre conjunto sintético.
- **Risco de fronteira:** a captura de 2026-09-03 pode mudar a estratégia de
  quebra e transformar o `section_summary` em metadado. Se isso for decidido
  antes desta fatia ser implementada, o recorte por `chunk_type` do relatório
  precisa ser revisto. As duas fatias são independentes: esta mede a quebra sem
  alterá-la.
- **Não aplicável — Interface:** este repositório não tem frontend, conforme
  `docs/frontend.md` e `INTERFACE.md`. A superfície é CLI. A demonstração
  gráfica pertence ao projeto-mãe pelo BACKLOG-0008.
- **Não aplicável — persistência nova:** o resultado é artefato de execução em
  `output/`, como o manifesto e a validação. Nenhuma informação nova precisa ser
  guardada de forma durável, então `$specsfy-data-discovery` não foi acionado.
- **Área encerrada:** descoberta concluída no limite de oito perguntas, sem
  lacuna aplicável remanescente.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** o pipeline não prova a qualidade do que prepara. O
   objetivo é um gate que bloqueie a indexação diante de falha determinística de
   integridade e publique, por documento, os sinais de qualidade que hoje passam
   silenciosos.
2. **Atores:** o operador que prepara a base e executa o pipeline; o mantenedor
   que ajusta as regras de chunking a partir do relatório.
3. **Escopo:** avaliação pré-indexação embutida no `pipeline.py`, comando próprio
   de diagnóstico, relatório legível, resultado estruturado por execução e testes
   das regras determinísticas e dos sinais heurísticos.
4. **Fora de escopo:** corrigir a origem, deduplicar, rechunkar, mudar a
   estratégia de chunking, histórico entre execuções, veredito automático de
   severidade e qualquer interface gráfica.
5. **Jornada essencial:** executar o pipeline; o gate avalia antes de indexar;
   invariante crítico interrompe sem escrever no destino; caso contrário indexa
   e publica os sinais por documento; o operador pode rodar o diagnóstico
   isolado enquanto ajusta o chunking.
6. **Aceite:** os oito cenários Given/When/Then desta entrada cobrem bloqueio por
   invariante, prosseguimento com sinal, agrupamento por documento, medição sobre
   conteúdo útil, derivação do máximo por documento, duplicata como sinal,
   diagnóstico isolado e separação em relação ao manifesto.
7. **Restrições:** somente regras determinísticas bloqueiam; leitura pura sem
   acesso remoto; sem segredos no relatório; nenhum limiar com identidade de
   cliente; `manifest.json` preserva sua responsabilidade única; Pytest com
   Red-Green-Refactor.
8. **Suposições confirmadas:** o gate roda entre chunking e indexação; o padrão
   de CLI da SPEC-0004 é reaproveitado; o mínimo é configurável e o máximo é
   derivado por documento.
9. **Decisões abertas:** nenhuma lacuna aplicável. Restam duas inferências a
   confirmar na especificação — comportamento no modo `--only-chunks` e os
   códigos de saída do comando de diagnóstico.

## Próximo passo

Promovido em 2026-09-03 para `specs/draft/0006-gate-qualidade-chunks-metadados/spec.md`.
Este item preserva a proveniência e a evidência da medição, mas deixa de
governar o comportamento: a fonte normativa é a spec.
