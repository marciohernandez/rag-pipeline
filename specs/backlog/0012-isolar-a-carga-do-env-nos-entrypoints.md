# Backlog: Isolar a carga do .env nos entrypoints

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0012 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Refinado em | 2026-09-03 |
| Spec promovida | specs/draft/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md (SPEC-0009) em 2026-09-03 |

## Ideia original

src/config.py chama load_dotenv() no import do módulo. Qualquer teste ou script que importe a configuração injeta o .env inteiro no processo. Isso já quebrou o teste de credencial ausente da SPEC-0003 quando OPENAI_API_KEY foi acrescentada ao .env: o teste passava isolado e falhava na suíte completa. Blindei o teste com monkeypatch, mas a causa continua. Mover a carga para os entrypoints resolveria, mas muda comportamento de produção usado por pipeline.py, search.py e chat.py.

## Problema percebido

`load_dotenv()` roda no corpo de `src/pipeline/config.py` (linha 13), fora de
qualquer função. Qualquer import da configuração — teste, script ou a futura
camada de aplicação — injeta o `.env` da máquina no processo inteiro. O efeito é
um acoplamento invisível: um teste que prova ausência de credencial passa ou
falha conforme qual módulo foi importado antes dele, e a regra de configuração
injetada estabelecida pela SPEC-0008 fica contornável enquanto essa chamada
existir.

## Pessoa afetada ou beneficiada

- Quem roda a suíte de testes: o resultado deixa de depender do conteúdo do
  `.env` local e da ordem de import.
- Marcio, como operador dos CLIs da raiz: a invocação dos comandos não muda.
- Quem implementar a fatia 2 (`src/app/`): a dívida bloqueante declarada na
  SPEC-0008 é removida.

## Resultado ou valor esperado

A carga do `.env` deixa de ser efeito colateral de biblioteca e passa a ser
responsabilidade explícita de cada entrypoint da raiz, por um bootstrap
compartilhado. `src/pipeline/` fica provadamente livre de `python-dotenv`, os
testes ficam determinísticos independentemente do `.env` da máquina e os CLIs
continuam resolvendo credencial exatamente como antes.

## Contexto

Dívida declarada como bloqueante no BACKLOG-0011 (Pergunta 5, 2026-09-03) e no
contrato publicado pela SPEC-0008 (`docs/architecture.md`, seção "Limites e
dívidas bloqueantes"): precisa ser resolvida antes de `src/app/` receber
implementação, porque um backend assíncrono chamando o pipeline agravaria o
acoplamento de estado global de ambiente. BACKLOG-0012 e BACKLOG-0013 podem ser
entregues em paralelo e não dependem um do outro.

Levantamento do código em 2026-09-03:

- `src/pipeline/config.py:13` chama `load_dotenv()` no import.
- Já chamam `load_dotenv()` no próprio `main()`: `chat.py`,
  `upsert_from_chunks.py`, `demo_rag.py` (redundante hoje).
- Dependem apenas do efeito colateral do import: `pipeline.py`, `search.py`,
  `validate.py`, `quality.py`, `inspect_chunks.py`, `main.py`.
- Leem ambiente para resolver credencial: `src/pipeline/config.py`
  (`get_openai_api_key`), `src/pipeline/providers/embeddings/openai.py`,
  `src/pipeline/providers/vectorstores/qdrant.py` e
  `src/pipeline/providers/vectorstores/pinecone.py`. Essa resolução permanece.
- Testes que já se blindam contra o `.env`: `tests/test_provider_factory.py` e
  `tests/test_characterization_providers.py` (`monkeypatch.delenv`);
  `tests/test_pipeline_service.py` já exige que a fachada não contenha
  `load_dotenv`.

## Referências relacionadas

- `specs/inbox/2026-09-02-195708-carregar-o-env-nos-entrypoints-em-vez-do-import-de-config.md`:
  captura de origem, preservada integralmente. Tipo: captura relacionada.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: declara este item como
  dívida bloqueante da fronteira interna entre pipeline e backend de aplicação.
  Tipo: backlog relacionado.
- `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md`: publica o
  contrato que registra esta dívida como impedimento da fatia 2 e define
  `PR-004` (resolução de credencial permanece nos providers). Tipo: spec
  relacionada.
- `specs/backlog/0013-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`:
  segunda dívida bloqueante, entregável em paralelo. Tipo: backlog relacionado.
- `docs/architecture.md`, seção "Limites e dívidas bloqueantes": destino da
  atualização documental. Tipo: documentação relacionada.
- `.specsfy/STACK.md`, linha "Configuração": destino da atualização documental.
  Tipo: documentação relacionada.

## Comportamento esperado

1. `src/bootstrap.py` expõe `load_env() -> None`: chama `load_dotenv()` do
   python-dotenv, é idempotente, não sobrescreve variável já presente no
   ambiente do processo e não levanta erro quando o arquivo `.env` não existe.
2. `src/pipeline/config.py` deixa de chamar `load_dotenv()` no import; nenhum
   módulo sob `src/pipeline/` importa `python-dotenv` ou chama `load_dotenv`.
3. Cada um dos nove entrypoints `.py` da raiz chama `load_env()` como primeira
   ação do fluxo de `main()`, antes de resolver `config.yaml`. Os três que hoje
   chamam `load_dotenv()` diretamente passam a chamar `load_env()`.
   `inspect_chunks.py`, que hoje roda código em nível de módulo, é
   reestruturado para o formato padrão de entrypoint — corpo dentro de
   `def main()` com bloco `if __name__ == "__main__": main()` — sem alterar seu
   comportamento de inspeção. `main.py` permanece no conjunto e recebe
   `load_env()` como os demais.
4. A resolução de credencial nos providers e em `get_openai_api_key` continua
   lendo variáveis já presentes no ambiente, sem alteração.
5. Um teste estático de AST reprova qualquer import de `dotenv` ou chamada a
   `load_dotenv` dentro de `src/pipeline/`, nomeando arquivo e import.
6. Um teste estático reprova qualquer `.py` executável da raiz (com bloco
   `if __name__ == "__main__"`) que não chame `load_env()` no fluxo de `main()`,
   nomeando o arquivo.
7. `docs/architecture.md` e `.specsfy/STACK.md` passam a descrever o bootstrap e
   a seção de dívidas bloqueantes registra BACKLOG-0012 como resolvida.

## Regras de negócio

- Código de biblioteca (`src/pipeline/`, incluindo a fachada `service.py` e os
  providers) nunca carrega o `.env`; apenas lê variáveis já presentes.
- A carga do `.env` é responsabilidade de entrypoint: todo `.py` executável da
  raiz chama `load_env()` antes de resolver configuração.
- `load_env()` não sobrescreve variável já definida no ambiente: CI e ambiente
  real prevalecem sobre o arquivo `.env`.
- A invocação dos cinco comandos de operação (`pipeline.py`, `search.py`,
  `chat.py`, `validate.py`, `upsert_from_chunks.py`) não muda.
- O contrato de `config.yaml` percebido pelo operador não muda.
- As blindagens `monkeypatch.delenv` dos testes de credencial ausente
  permanecem como garantia por caso, mesmo com a causa raiz removida.

## Critérios de aceitação

```gherkin
Scenario: Importar o pipeline não injeta o .env
  Given nenhum entrypoint foi executado
  When um teste importa src.pipeline.config ou outro módulo de src/pipeline/
  Then nenhuma variável do .env é injetada no processo pelo import
  And o teste de "credencial ausente" não depende da ordem de import nem do .env da máquina

Scenario: Os comandos de operação resolvem credencial como antes
  Given um .env válido no diretório de trabalho
  When o operador executa cada um dos cinco comandos de operação
  Then load_env() é chamado antes da resolução de configuração
  And a credencial é resolvida do .env exatamente como antes da mudança
  And a invocação de cada comando é idêntica

Scenario: Fronteira estática mantém src/pipeline/ livre de dotenv
  Given a suíte é executada
  When o teste estático varre a AST de cada módulo sob src/pipeline/
  Then reprova se algum importar dotenv ou chamar load_dotenv
  And a mensagem nomeia o arquivo e o import

Scenario: Todo entrypoint da raiz carrega o ambiente
  Given a suíte é executada
  When o teste estático varre cada .py executável da raiz
  Then reprova se algum não chamar load_env() no fluxo de main()
  And a mensagem nomeia o arquivo

Scenario: load_env() é idempotente e não sobrescreve
  Given OPENAI_API_KEY já presente no ambiente do processo
  When load_env() é chamado, inclusive duas vezes
  Then o valor já presente no ambiente é preservado
  And nenhum erro é levantado quando o arquivo .env não existe

Scenario: Regressão completa
  Given a mudança concluída
  When uv run pytest e uv run ruff check . são executados
  Then a suíte permanece verde com contagem maior ou igual a 255
  And o ruff não acusa nada
```

## Qualidades e operação

- Segurança: sem nova superfície de segredo. A resolução de credencial não
  muda; `.env` continua fora do repositório. A mudança melhora o isolamento ao
  tirar o `.env` do caminho de import de biblioteca.
- Privacidade: não aplicável; nenhum dado pessoal é tocado.
- Desempenho e volume: efeito desprezível; move uma chamada de função.
- Auditoria e observabilidade: sem mudança de log. Os dois testes estáticos
  tornam a regra verificável a cada push, no mesmo padrão da fronteira da
  SPEC-0003 e da SPEC-0008.

## Dependências

- `python-dotenv` continua sendo a dependência de carga; muda apenas o ponto de
  chamada. Nenhuma dependência nova.
- Nenhuma dependência de outro item de backlog. BACKLOG-0013 é paralelo.

## Situações de erro

- Entrypoint executado sem `.env` no diretório → `load_env()` é no-op; a
  resolução de credencial posterior falha com o erro claro já existente, sem
  regressão.
- `load_env()` chamado mais de uma vez no mesmo processo → idempotente, sem
  erro.
- Entrypoint novo adicionado à raiz sem `load_env()` → o teste estático reprova,
  nomeando o arquivo.
- Módulo de `src/pipeline/` que volte a importar `dotenv` → o teste estático de
  AST reprova, nomeando arquivo e import.

## Escopo

- Dentro: criar `src/bootstrap.py` com `load_env()`; remover `load_dotenv()` de
  `src/pipeline/config.py`; os nove entrypoints da raiz chamam `load_env()` no
  início do `main()` (três trocam o `load_dotenv()` redundante); reestruturar
  `inspect_chunks.py` para o formato padrão de entrypoint sem mudar seu
  comportamento; dois testes estáticos; atualizar `docs/architecture.md`,
  `.specsfy/STACK.md` e `.specsfy/RULES.md`.
- Fora: implementar `src/app/` ou o bootstrap de ambiente do backend; mudar a
  resolução de credencial nos providers; mudar o contrato de `config.yaml`
  percebido pelo operador; resolver BACKLOG-0013.

## Dúvidas, decisões e riscos

- Decisão confirmada na Pergunta 1 (2026-09-03): a carga do `.env` fica em um
  bootstrap compartilhado fora de `src/pipeline/`, chamado por cada entrypoint,
  com teste estático proibindo `dotenv` em `src/pipeline/**`. Alternativas
  descartadas: cada CLI chamar `load_dotenv()` diretamente sem módulo comum
  (repete a linha, depende de ninguém esquecer); bootstrap em `src/app/`
  (acopla os CLIs à futura camada de aplicação).
- Decisão confirmada na Pergunta 2 (2026-09-03): todos os nove entrypoints da
  raiz chamam `load_env()`, não só os cinco operacionais. Motivo: elimina o
  risco de entrypoint esquecido apontado na Inbox; o custo é uma linha por
  arquivo e um teste estático torna a regra verificável.
- Decisão confirmada na Pergunta 4 (2026-09-03, retomada por BLOCKER da
  validação da SPEC-0009): `inspect_chunks.py` — hoje sem `main()` nem bloco
  `if __name__ == "__main__"` — é reestruturado para o formato padrão de
  entrypoint nesta entrega, sem alterar seu comportamento de inspeção; `main.py`
  permanece no conjunto de nove e recebe `load_env()`. Motivo: mantém a decisão
  da Pergunta 2 ao pé da letra, com nove entrypoints e o critério simples
  `if __name__ == "__main__"` no teste estático. Alternativas descartadas:
  remover `main.py` como código morto (mexe numa decisão já confirmada e
  espalha para `docs/README.md`); alargar o teste estático para detectar código
  executável em nível de módulo (teste mais complexo sem ganho).
- Decisão confirmada na Pergunta 3 (2026-09-03): o módulo é `src/bootstrap.py`,
  expondo `load_env() -> None`, idempotente e sem override de variável já
  presente. Alternativas descartadas: `bootstrap.py` na raiz (fora do pacote
  `src/`); `src/env.py` (nome menos descritivo).
- Risco: `python-dotenv` procura `.env` subindo a partir do diretório de
  trabalho; um operador que rode o CLI de outra pasta pode não carregar o
  `.env` esperado. Mitigação: `load_env()` mantém o comportamento padrão do
  `load_dotenv()` já em uso hoje; nenhuma mudança de resolução de caminho.
- Nenhuma lacuna aplicável permanece.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** tirar `load_dotenv()` do import de
   `src/pipeline/config.py` e tornar a carga do `.env` responsabilidade
   explícita dos entrypoints da raiz, por um bootstrap compartilhado.
2. **Atores:** quem roda a suíte; Marcio como operador dos CLIs; implementador
   da fatia 2.
3. **Escopo:** `src/bootstrap.py` com `load_env()`; remoção da chamada em
   `config.py`; nove entrypoints chamando `load_env()`, com `inspect_chunks.py`
   reestruturado para o formato padrão; dois testes estáticos; atualização de
   `docs/architecture.md`, `.specsfy/STACK.md` e `.specsfy/RULES.md`. Fora:
   `src/app/`, resolução de credencial, contrato de `config.yaml`,
   BACKLOG-0013.
4. **Jornada essencial:** `src/pipeline/` livre de `dotenv`; todo entrypoint da
   raiz chama `load_env()` antes de resolver configuração; `load_env()`
   idempotente e sem override; credencial resolvida do ambiente já presente.
5. **Aceite:** seis cenários Given/When/Then cobrindo import sem injeção,
   comandos inalterados, fronteira estática de `src/pipeline/`, cobertura de
   todos os entrypoints, idempotência de `load_env()` e regressão completa.
6. **Restrições:** `python-dotenv` continua a dependência; suíte ≥ 255; ruff
   limpo; invocação dos cinco comandos inalterada; blindagens `monkeypatch`
   preservadas.
7. **Suposições:** `main.py`, `inspect_chunks.py` e `quality.py` recebem
   `load_env()` pela regra uniforme; entrypoint da raiz = `.py` com
   `if __name__ == "__main__"`; runner permanece Pytest.
8. **Effort provável:** 3.
9. **Decisões abertas:** nenhuma.

## Próximo passo

Promover com `$specsfy-03-specify` para criar a spec normativa inicial em
`specs/draft/0012-isolar-a-carga-do-env-nos-entrypoints/spec.md`, preservando
`Definition Gate: Pending` até a validação do Ato I.
