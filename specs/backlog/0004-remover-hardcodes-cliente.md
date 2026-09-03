# Backlog: Remover hardcodes de cliente e tornar ferramentas configuráveis

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0004 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Configuração operacional reutilizável |
| Tipo | Melhoria técnica |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-08-31 |
| Refinado em | 2026-09-02 |
| Spec promovida | `specs/defined/0005-remover-hardcodes-cliente/spec.md` |

## Ideia original

Eliminar referências fixas à C6 e à Vivo dos CLIs, demos e verificadores, usando configuração e exemplos neutros.

## Problema percebido

Scripts operacionais e demonstrações contêm branding, conteúdo e nomes de collection específicos, criando risco de uso no destino errado e acoplamento ao caso atual.

Refinamento de 2026-09-02, por varredura do código: são oito ocorrências, não
cinco. Cinco nomeiam o cliente antigo e três acoplam sem nomeá-lo, por conteúdo
do domínio bancário. A mais grave das três é comportamento executável, não
comentário: `demo_rag.py:27` define `PERGUNTA_PADRAO` como uma pergunta sobre
cheque especial, de modo que `uv run python demo_rag.py` sem argumento consulta
a base de telecom configurada perguntando sobre um produto bancário.

Há ainda uma camada além do código: `config.yaml` é versionado com dez valores
de um cliente real como default do repositório, incluindo `collection_name` e
`namespace`, que endereçam o destino remoto. É daí que vem o "risco de uso no
destino errado" declarado acima.

## Pessoa afetada ou beneficiada

Operadores que reutilizam o pipeline para diferentes clientes e bases.

## Resultado ou valor esperado

Toda ferramenta operacional funciona por configuração explícita e os exemplos não confundem dados de demonstração com defaults do produto.

## Contexto

Item P1 do milestone M0, dependência declarada do BACKLOG-0007, que encerra o
milestone. Ocorrências localizadas em `chat.py`, `demo_rag.py` e `search.py`.

Contexto corrigido em 2026-09-02: a formulação anterior citava
`scripts/check_qdrant_connection.py`, removido pela SPEC-0004 no commit
`2b3eddf`, e não mencionava `search.py`, onde há duas ocorrências.

## Referências relacionadas

- `chat.py`, `demo_rag.py` e `search.py`: as oito ocorrências desta fatia.
- `config.yaml` e `src/config.py`: mecanismo de configuração existente.
- `.env` e `.env.example`: precedente do repositório para separar valor local de
  exemplo versionado, adotado como padrão nesta fatia.
- `tests/test_validation_boundaries.py`: guarda estática existente, com lista de
  identificadores de cliente aplicada ao código de validação. Precedente a
  estender.
- `tests/test_docs_safety.py`: inclui `config.yaml` na varredura de material
  publicado; muda junto com o arquivo.
- `GUIA_DE_USO.md`, linha 576: documentação relacionada, que hoje registra a
  limitação como conhecida e deixa de ser verdadeira com esta entrega.
- `specs/completed/0004-validar-recuperacao-operacao/spec.md`: spec relacionada.
  Seu AC-014 removeu identificadores de cliente somente do código de validação,
  e seu gabarito depende de `documentos/`, mantido fora do escopo aqui.
- `specs/backlog/0010-provider-llm-plugavel.md`: backlog relacionado. Também
  toca `chat.py`, mas trata de trocar o provider de LLM por configuração;
  escopos a manter separados.
- `specs/backlog/0007-gates-entrega-handoff.md`: declara este item como
  dependência.
- Linear `LEAD-87`: tracking do item no milestone M0.

## Comportamento esperado

- As ferramentas derivam a identidade da base de `projeto.nome` e
  `projeto.descricao`, já existentes em `config.yaml`. Nenhum campo novo é
  criado. A escolha é coerente com o código atual, que já lê `projeto.nome`
  para montar o escopo de busca e só mantém a identidade fixa na geração.
- `chat.py` apresenta a base e monta o prompt do sistema a partir desses dois
  valores.
- `demo_rag.py` monta o prompt demonstrado a partir dos mesmos valores e usa,
  como pergunta padrão, a primeira consulta declarada no gabarito de
  `caminhos.consultas_referencia`.
- `search.py` traz exemplos de uso neutros, sem pergunta de domínio de cliente.
- `config.example.yaml` neutro passa a ser versionado e `config.yaml` entra no
  `.gitignore`, espelhando o par `.env.example` e `.env` já adotado.

## Regras de negócio

- `projeto.nome` continua obrigatório, como já é hoje em `build_scope` e em
  `validate.py`; sua ausência encerra a execução com mensagem clara.
- `projeto.descricao` ausente ou vazia degrada para descrição neutra, com aviso
  ao operador.
- Gabarito ausente no caminho declarado degrada para pergunta neutra, com aviso
  ao operador, sem falhar.
- A degradação é proporcional ao risco: as três ferramentas são somente
  leitura, e a política fail-closed do repositório, vinda da SPEC-0001, protege
  mutação de estado remoto, não apresentação de texto.
- Nenhum identificador de cliente permanece escrito no código das ferramentas
  operacionais, seja nome próprio ou conteúdo de domínio.

## Critérios de aceitação

- **AC1** — Dada uma configuração com `projeto.nome` e `projeto.descricao`
  arbitrários, quando o operador inicia `chat.py`, então a mensagem de abertura
  e o prompt do sistema citam esses valores e nenhum identificador de outro
  cliente aparece na saída.
- **AC2** — Dados `chat.py`, `demo_rag.py` e `search.py`, quando a guarda
  estática varre seus textos, então nenhum identificador de cliente conhecido é
  encontrado.
- **AC3** — Dada uma configuração cujo gabarito declara uma pergunta como
  primeira consulta, quando o operador executa `demo_rag.py` sem argumento,
  então essa é a pergunta usada.
- **AC4** — Dada uma configuração sem gabarito no caminho declarado, quando o
  operador executa `demo_rag.py` sem argumento, então uma pergunta neutra é
  usada, o operador é avisado e o comando não falha.
- **AC5** — Dada uma configuração com `projeto.descricao` vazia, quando o
  operador inicia `chat.py`, então uma descrição neutra é usada e o operador é
  avisado.
- **AC6** — Dada uma configuração sem `projeto.nome`, quando o operador executa
  qualquer uma das três ferramentas, então a execução falha com mensagem clara.
- **AC7** — Dado o repositório, quando se inspeciona o índice do Git, então
  `config.yaml` não está versionado, `config.example.yaml` está, e o exemplo não
  contém identificador de cliente nem destino remoto real.

## Qualidades e operação

- Segurança: a fatia retira do controle de versão o endereçamento do destino
  remoto de um cliente — `collection_name` e `namespace`. Credenciais já ficam
  fora do repositório e não são tocadas aqui.
- Privacidade: nenhum dado pessoal é processado. O conteúdo do cliente em
  `documentos/` permanece fora do escopo.
- Desempenho e volume: sem efeito. As mudanças são de texto, configuração e
  testes.
- Auditoria e observabilidade: os avisos de degradação informam ao operador
  quando a identidade apresentada é neutra em vez de derivada da configuração.

## Dependências

- Nenhuma dependência bloqueante. `documentos/` e o gabarito criados pela
  SPEC-0004 são insumo da pergunta padrão, e já existem.

## Situações de erro

- `projeto.nome` ausente: falha com mensagem clara, em qualquer das três
  ferramentas.
- `projeto.descricao` ausente ou vazia: descrição neutra e aviso.
- Gabarito inexistente no caminho declarado: pergunta neutra e aviso.
- Gabarito existente porém vazio ou malformado: mesmo tratamento do inexistente;
  a validação estrita do gabarito pertence a `validate.py`, não ao demo.

## Escopo

- **Dentro**: as oito ocorrências em `chat.py`, `demo_rag.py` e `search.py`;
  criação de `config.example.yaml` neutro versionado e entrada de `config.yaml`
  no `.gitignore`, com `git rm --cached`; guarda positiva de derivação e
  extensão da lista de proibições existente aos CLIs; atualização de
  `GUIA_DE_USO.md` linha 576, do README quanto ao passo de cópia da
  configuração, e de `tests/test_docs_safety.py` quanto ao arquivo varrido.
- **Fora**: `documentos/`, cuja base foi validada pela SPEC-0004 e de quem o
  gabarito e o manifesto dependem; a troca do provider de LLM e a fronteira
  `ChatOpenAI` de `chat.py`, que pertencem ao BACKLOG-0010; qualquer
  funcionalidade do MVP do projeto-mãe.

## Dúvidas, decisões e riscos

- Decisão confirmada em 2026-09-02: a identidade vem de `projeto.nome` e
  `projeto.descricao`, sem criar campo novo em `config.yaml`.
- Decisão confirmada em 2026-09-02: o escopo cobre código e `config.yaml`, e não
  `documentos/`.
- Decisão confirmada em 2026-09-02: `config.example.yaml` neutro versionado e
  `config.yaml` no `.gitignore`, espelhando o padrão do `.env`.
- Decisão confirmada em 2026-09-02: duas guardas de regressão, com o teste
  positivo de derivação como principal e a lista de proibições como rede. A
  lista sozinha só pega o nome que alguém lembrar de listar e não protegeria
  contra um cliente futuro.
- Decisão confirmada em 2026-09-02: a pergunta padrão do `demo_rag.py` vem da
  primeira consulta do gabarito.
- Decisão confirmada em 2026-09-02: degradação proporcional ao risco, com
  `projeto.nome` obrigatório e os demais campos degradando com aviso.
- Risco: a saída de `config.yaml` do índice exige um passo de cópia para quem
  clonar o repositório. Mitigado documentando o passo no README e no
  `GUIA_DE_USO.md`, como já ocorre com `.env.example`.
- Suposição: `git rm --cached config.yaml` preserva o arquivo em disco, então a
  configuração local em uso não é afetada.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido em 2026-09-02 para `specs/defined/0005-remover-hardcodes-cliente/spec.md`. A partir daqui a spec governa o comportamento; este item preserva apenas a proveniência do refinamento.
