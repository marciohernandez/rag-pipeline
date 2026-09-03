# Verificações locais — SPEC-0005

Notas de proveniência das inspeções feitas no próprio repositório em
2026-09-02, durante o refinamento do BACKLOG-0004 e a promoção desta spec.
Nenhuma fonte externa foi consultada: cada conclusão vem de comando executado
localmente, reproduzível a partir da raiz do projeto.

Este arquivo é evidência não normativa. As conclusões que governam a entrega
vivem em `spec.md`.

## R-001 — Inventário das ocorrências de acoplamento a cliente

Duas varreduras foram necessárias, e a diferença entre elas é o achado.

Varredura por nome do cliente:

```bash
grep -rniE 'c6|vivo|gold' --include='*.py' . \
  --exclude-dir=.venv --exclude-dir=tests --exclude-dir=__pycache__
```

Resultado: cinco ocorrências — `search.py:11`, `chat.py:63`, `chat.py:94`,
`chat.py:116` e `demo_rag.py:94`.

Varredura ampliada para conteúdo do domínio bancário, sem o nome:

```bash
grep -rniE 'cheque especial|conta PJ|banco|bank|empresas|fatura|taxa' \
  --include='*.py' . \
  --exclude-dir=.venv --exclude-dir=tests --exclude-dir=__pycache__
```

Resultado: oito ocorrências. As três adicionais são `search.py:10` e
`demo_rag.py:11`, ambas em docstring, e `demo_rag.py:27`, que define
`PERGUNTA_PADRAO = "qual a taxa do cheque especial?"`.

Consequência para a spec: `demo_rag.py:27` é a mais grave das três, por ser
comportamento executável e não comentário — `uv run python demo_rag.py` sem
argumento consulta a base de telecomunicações configurada perguntando sobre um
produto bancário. O inventário do backlog citava cinco ocorrências e foi
corrigido para oito. A guarda estática precisa alcançar as duas formas de
acoplamento.

## R-002 — Dependência da suíte em relação a `config.yaml`

```bash
grep -rn "config.yaml" tests/
```

Resultado: uma única referência, em `tests/test_docs_safety.py:20`, que inclui
o arquivo na lista de material publicado varrido em busca de comando
destrutivo. Nenhum teste lê valores desse arquivo.

Consequência para a spec: retirar `config.yaml` do controle de versão não
quebra a suíte; exige apenas trocar o alvo daquela varredura para o exemplo
versionado. Registrado em FR-006 e AC-014.

## R-003 — Precedente local de separação entre valor de uso e exemplo

```bash
cat .gitignore
git ls-files --error-unmatch .env
```

Resultado: `.gitignore` contém `.env` sob o comentário
`# Segredos — NUNCA commitar`, e `.env` não está versionado; apenas
`.env.example` está.

Verificação complementar do estado atual da configuração:

```bash
git ls-files --error-unmatch config.yaml
grep -niE 'vivo|gold' config.yaml | grep -v '^\s*#'
```

Resultado: `config.yaml` está versionado e contém dez valores de um cliente
real fora de comentários, entre eles `collection_name` na linha 132 e
`namespace` na linha 143, que endereçam o destino remoto.

Consequência para a spec: o par `.env` e `.env.example` é o precedente adotado
em DEC-003. A presença do endereçamento remoto no índice do Git é a evidência
concreta do risco de uso no destino errado declarado pelo BACKLOG-0004.

## R-004 — Guarda existente contra identificador de cliente

Leitura de `tests/test_validation_boundaries.py`.

Resultado: o arquivo mantém, a partir da linha 31, uma tupla
`IDENTIFICADORES_DE_CLIENTE` com três entradas, verificada contra um conjunto
fixo de arquivos do código de validação. A tupla não inclui o cliente antigo,
porque o AC-014 da SPEC-0004 limitou-se ao código de validação.

Consequência para a spec: o padrão é reaproveitado e estendido às três
ferramentas, mas não basta sozinho. Uma lista alcança apenas o identificador
que alguém registrar nela e não protegeria contra um cliente futuro, o que
motivou a guarda positiva de derivação em DEC-004 e NFR-003.

## R-005 — Coerência atual entre busca e apresentação

Leitura integral de `chat.py`, `demo_rag.py` e `search.py`.

Resultado: as três já derivam o escopo de busca da configuração, com
`build_scope(cfg["projeto"]["nome"], args.tenant)` em `chat.py:69`,
`demo_rag.py:55` e `search.py:55`. A identidade fixa sobrevive apenas na
apresentação ao operador e na montagem do prompt.

Consequência para a spec: a correção é local e não exige tocar o fluxo de
recuperação, o que sustenta o item correspondente em `Fora de escopo` e a
avaliação de Effort 4.
