# Guia de uso do Pipeline RAG

Este guia mostra como preparar documentos Markdown, gerar chunks, criar embeddings e indexar uma base no Qdrant sem misturar projetos ou duplicar pontos.

## 1. Como o sistema funciona

O pipeline executa este fluxo:

```text
Documentos .md
    -> chunks (pedacos menores com metadados)
    -> embeddings (representacoes numericas do texto)
    -> collection no Qdrant
```

Cada projeto deve ter:

- uma pasta propria de documentos;
- uma pasta propria de saida;
- um nome de collection exclusivo no Qdrant.

Exemplo atual:

```text
documentos/vivo_gold_banda_larga_pf/
output/vivo_gold_banda_larga_pf/
collection: vivo_gold_banda_larga_pf
```

## 2. Preparar o ambiente no WSL

Abra o terminal WSL e entre no projeto:

```bash
cd /mnt/f/Projetos/rag-ingestion-pipeline
```

Na primeira instalacao, use Python 3.12 e instale as dependencias. No WSL, manter o ambiente virtual no filesystem Linux evita lentidão ao copiar pacotes para uma unidade montada do Windows:

```bash
export UV_PROJECT_ENVIRONMENT="/home/$USER/.venvs/rag-ingestion-pipeline"
uv sync --python 3.12 --all-groups --locked --link-mode=copy
```

Ative o ambiente em cada novo terminal:

```bash
source "$UV_PROJECT_ENVIRONMENT/bin/activate"
```

Confirme o ambiente:

```bash
python -c "import sys; print(sys.executable); print(sys.version); print(sys.platform)"
```

O executável deve pertencer ao ambiente configurado, a versão deve ser 3.12 ou superior e a plataforma deve ser `linux`.

Nao execute `uv init`: o projeto ja possui `pyproject.toml`.

## 3. Configurar as credenciais

O arquivo `.env` guarda somente endpoints e credenciais. Nunca envie esse arquivo ao Git.

Para a configuracao atual, os campos importantes sao:

```dotenv
OPENAI_API_KEY=...
QDRANT_URL=https://qdrant.bigdates.com.br
QDRANT_API_KEY=...
```

Nao coloque o nome da collection no `.env`. Esse nome pertence ao `config.yaml`.

## 4. Organizar os documentos

Coloque todos os arquivos da mesma base em uma pasta exclusiva:

```text
documentos/
├── vivo_gold_banda_larga_pf/
│   ├── ofertas.md
│   ├── beneficios.md
│   └── procedimentos.md
├── vivo_fibra_pj/
└── c6_empresas/
```

O carregador atual:

- aceita somente arquivos `.md`;
- processa todos os `.md` diretamente dentro da pasta configurada;
- nao percorre subpastas;
- envia todos os arquivos da execucao para a mesma collection.

Nao misture clientes, produtos ou bases diferentes na mesma pasta.

## 5. Configurar o projeto no `config.yaml`

Ao trocar de base, revise principalmente:

```yaml
projeto:
  nome: "Vivo_Gold_Banda_Larga_PF"
  descricao: "Base de conhecimento Gold para Banda Larga de pessoas fisicas."

caminhos:
  input_dir: "./documentos/vivo_gold_banda_larga_pf"
  output_dir: "./output/vivo_gold_banda_larga_pf"
  chunks_file: "./output/vivo_gold_banda_larga_pf/chunks.json"
  vector_store_dir: "./output/vivo_gold_banda_larga_pf/chroma_db"

embedding:
  provider: "openai"
  model: "text-embedding-3-small"
  batch_size: 50

vector_store:
  provider: "qdrant"
  collection_name: "vivo_gold_banda_larga_pf"
  sync_mode: "mirror"

log:
  level: "INFO"
  arquivo: "./output/vivo_gold_banda_larga_pf/pipeline.log"
```

Regras importantes:

- `input_dir`, `output_dir`, `chunks_file`, log e `collection_name` devem corresponder ao mesmo projeto;
- use um `collection_name` exclusivo, sem espacos ou acentos;
- nao troque o modelo de embedding dentro de uma collection preenchida;
- `text-embedding-3-small` usa vetores de 1536 dimensoes.
- `sync_mode: "mirror"` considera a pasta de entrada como fonte de verdade e remove pontos obsoletos somente depois de um upsert bem-sucedido.

O proprio `config.yaml` possui comentarios detalhados sobre cada campo.

## 6. Metadados dos chunks

O pipeline adiciona automaticamente:

- `nome_arquivo`;
- `caminho_relativo`;
- `titulo`, extraido de `#`;
- `secao`, extraida de `##`, quando existir;
- `subsecao`, extraida de `###`, quando existir;
- `breadcrumb`, como `[Titulo > Secao > Subsecao]`;
- `chunk_index`;
- `total_chunks`.
- `project_id`, `document_id`, `source_hash` e `chunk_id`, usados para sincronização segura;
- `chunk_type`, com valor `detail` ou `section_summary`.

### Resumos automáticos de seção

Quando `chunking.generate_section_summaries` estiver ativo, o pipeline cria um `section_summary` para cada seção `##` com pelo menos `section_summary_min_children` subseções `###` distintas. O resumo lista os títulos na ordem original e é sempre derivado novamente dos Markdown atuais. Não crie nem mantenha um arquivo de resumo manual.

Exemplo:

```text
[Vivo Fibra > Planos Vivo Fibra]

Itens disponíveis nesta seção:
- Vivo Fibra 500 MEGA
- Vivo Fibra 600 MEGA
- Vivo Fibra 1 GIGA
```

Voce pode adicionar metadados a todos os chunks de um documento usando frontmatter no inicio do `.md`:

```yaml
---
produto: "Vivo Fibra"
publico: "Pessoa Fisica"
categoria: "Ofertas"
fonte: "Documento comercial"
data_atualizacao: "2026-07-01"
---

# Titulo do documento

Conteudo do documento...
```

O frontmatter tambem pode ajustar apenas aquele arquivo:

```yaml
---
splitter: "header"
chunk_size_recommended: 1200
chunk_overlap_recommended: 200
---
```

## Como preparar um arquivo `.md` para uma boa recuperacao

Um documento bem preparado costuma melhorar mais a recuperacao do que simplesmente aumentar a quantidade de chunks. Cada trecho deve conseguir responder a uma pergunta mesmo quando for recuperado separado do restante do arquivo.

### Estrutura recomendada

Use esta hierarquia:

```markdown
# Nome do produto ou assunto principal

Breve explicacao sobre o que este documento cobre.

## Tema ou etapa

### Pergunta, regra ou procedimento especifico

Resposta completa e objetiva.
```

No pipeline atual:

- `#` vira o metadata `titulo`;
- `##` vira `secao`;
- `###` vira `subsecao`;
- esses campos formam o `breadcrumb` incluído no texto do chunk.

Use apenas um titulo `#` principal por documento. Organize os assuntos em `##` e as perguntas ou regras especificas em `###`.

### Escreva secoes independentes

Evite trechos que dependam de frases vagas como:

```text
Ele tambem possui esse beneficio nas mesmas condicoes acima.
```

Prefira repetir o contexto essencial:

```text
O cliente Vivo Fibra 600 Mega tambem possui o beneficio Amazon Prime por seis meses, nas mesmas condicoes descritas nesta oferta.
```

Quando o chunk aparece sozinho em uma busca, a segunda versao continua compreensivel.

### Use os termos que as pessoas pesquisam

Inclua no titulo ou no texto:

- nome oficial do produto;
- nomes populares e siglas relevantes;
- tipo de cliente, como PF ou Pessoa Fisica;
- acao procurada, como contratar, cancelar, instalar ou consultar;
- valores, prazos, elegibilidade e restricoes importantes.

Exemplo:

```markdown
### Prazo de instalacao do Vivo Fibra para Pessoa Fisica

A instalacao do Vivo Fibra PF ocorre...
```

Isso e melhor para recuperacao do que um titulo generico como `### Prazo`.

### Uma pergunta ou intencao principal por subsecao

Evite colocar preco, cancelamento, instalacao e beneficios em um unico bloco longo. Separe:

```markdown
## Vivo Fibra 600 Mega

### Preco e condicoes de pagamento

...

### Beneficios incluidos

...

### Prazo e regras de instalacao

...

### Cancelamento e fidelidade

...
```

Essa estrutura permite recuperar apenas o trecho que responde a pergunta.

### Tamanho das secoes

Com `default_chunk_size: 1000`, tente manter cada subsecao entre aproximadamente 300 e 900 caracteres quando isso for natural.

- secoes muito pequenas podem perder contexto;
- secoes muito grandes serao divididas automaticamente;
- nao aumente texto artificialmente apenas para atingir um tamanho;
- listas curtas e respostas objetivas podem ter menos de 300 caracteres.

### Listas e procedimentos

Use listas para requisitos, beneficios e passos:

```markdown
### Como solicitar a instalacao

1. Confirme a disponibilidade no endereco.
2. Escolha o plano.
3. Informe os dados do titular.
4. Agende a visita tecnica.
```

Repita no titulo e na introducao qual produto ou processo a lista descreve.

### Tabelas

Tabelas Markdown podem ser usadas para comparacoes simples:

```markdown
| Plano | Download | Upload | Preco base |
|---|---:|---:|---:|
| Vivo Fibra 500 Mega | 500 Mbps | 250 Mbps | R$ 100,00 |
```

Para tabelas grandes ou complexas, considere transformar cada produto em uma subsecao textual. Isso evita que cabecalhos e valores sejam separados durante o chunking.

### Datas, valores e vigencia

Escreva datas e unidades de forma explicita:

```text
Oferta valida de 1 de julho de 2026 a 31 de julho de 2026.
Mensalidade: R$ 120,00 por mes.
Download: 600 Mbps. Upload: 300 Mbps.
```

Evite expressoes como `neste mes`, `amanha`, `valor acima` ou `regra anterior`, pois o trecho pode ser consultado fora do contexto original.

### Links e fontes

Links podem permanecer no corpo, mas registre tambem a origem no frontmatter. Se uma informacao possuir validade juridica ou comercial, inclua a data de atualizacao e a vigencia.

### Frontmatter recomendado

O frontmatter precisa ser o primeiro conteudo do arquivo, delimitado por `---`:

```yaml
---
documento_id: "vivo-fibra-pf-ofertas-2026-07"
produto: "Vivo Fibra"
publico: "Pessoa Fisica"
categoria: "Ofertas"
tipo_documento: "Tabela comercial"
fonte: "Material comercial Vivo"
data_atualizacao: "2026-07-01"
inicio_vigencia: "2026-07-01"
fim_vigencia: "2026-07-31"
versao: "2026-07"
status: "vigente"
splitter: "header"
chunk_size_recommended: 1000
chunk_overlap_recommended: 200
---
```

Significado dos campos sugeridos:

| Campo | Para que serve | Exemplo |
|---|---|---|
| `documento_id` | Identificador estavel e exclusivo do documento | `vivo-fibra-pf-ofertas-2026-07` |
| `produto` | Produto principal | `Vivo Fibra` |
| `publico` | Segmento atendido | `Pessoa Fisica` |
| `categoria` | Grupo de assunto | `Ofertas`, `Beneficios`, `Regulamento` |
| `tipo_documento` | Natureza da fonte | `FAQ`, `Contrato`, `Tabela comercial` |
| `fonte` | Origem da informacao | `Site Vivo`, `Material comercial Vivo` |
| `data_atualizacao` | Data da ultima revisao | `2026-07-01` |
| `inicio_vigencia` | Inicio da validade, quando aplicavel | `2026-07-01` |
| `fim_vigencia` | Fim da validade, quando aplicavel | `2026-07-31` |
| `versao` | Versao humana do documento | `2026-07` |
| `status` | Situacao do conteudo | `vigente`, `expirado`, `rascunho` |
| `splitter` | Estrategia especifica do arquivo | `header` |
| `chunk_size_recommended` | Tamanho especifico dos chunks | `1000` |
| `chunk_overlap_recommended` | Sobreposicao especifica | `200` |

Use nomes de campos consistentes em todos os documentos. Prefira valores simples como texto, numero ou booleano e evite estruturas YAML aninhadas.

Listas no frontmatter sao aceitas pelo carregador, mas sao convertidas em uma string separada por virgulas. Exemplo:

```yaml
tags:
  - fibra
  - internet
  - pessoa fisica
```

Sera armazenado aproximadamente como:

```text
tags: "fibra, internet, pessoa fisica"
```

### Frontmatter nao substitui o conteudo

Os metadados acompanham o chunk e podem ser usados para identificar a fonte ou aplicar filtros. Entretanto, a busca vetorial do projeto gera o embedding principalmente a partir de `page_content`.

Portanto, se `produto: "Vivo Fibra"` existir apenas no frontmatter, isso nao garante que uma pergunta contendo `Vivo Fibra` encontre aquele chunk. Inclua os termos importantes tambem nos headings ou no texto.

### O que remover antes de indexar

Remova ou corrija:

- menus, rodapes e textos de navegacao copiados de sites;
- conteudo duplicado;
- paginas sem relacao com a base;
- informacoes vencidas sem marcacao clara;
- caracteres corrompidos, como `Ã§` no lugar de `ç`;
- referencias vagas a imagens ou anexos ausentes;
- dados pessoais e segredos que nao devem chegar ao Qdrant.

### Modelo reutilizavel

Ha um arquivo pronto em [`modelos/MODELO_DOCUMENTO_RAG.md`](modelos/MODELO_DOCUMENTO_RAG.md). Copie-o para a pasta do projeto, renomeie e substitua os exemplos pelo conteudo real.

## 7. Validar os chunks sem indexar

Sempre execute primeiro:

```bash
python pipeline.py --only-chunks
```

Esse comando:

- le os documentos;
- gera os chunks;
- sobrescreve o `chunks.json` do projeto;
- gera e valida também o `manifest.json` ao lado do `chunks.json`;
- nao gera embeddings;
- nao cria, apaga ou altera collections no Qdrant.

Abra o arquivo configurado em `caminhos.chunks_file` e confira:

- se todos os documentos esperados aparecem;
- se o texto esta legivel;
- se `titulo`, `secao`, `subsecao` e `breadcrumb` fazem sentido;
- se os metadados de frontmatter foram herdados;
- se os chunks nao ficaram pequenos ou grandes demais.
- se os `section_summary` esperados foram criados;
- se a contagem e os IDs do manifesto são únicos.

## 8. Conferir a collection antes de indexar

Use este comando para consultar a collection configurada, sem alterar dados:

```bash
python - <<'PY'
from dotenv import load_dotenv
from src.config import load_config
from src.embedder import _get_qdrant_client

load_dotenv(".env")
cfg = load_config("config.yaml")
name = cfg["vector_store"]["collection_name"]
client = _get_qdrant_client()

exists = client.collection_exists(name)
print("Collection:", name)
print("Existe:", exists)
if exists:
    print("Pontos:", client.count(collection_name=name).count)
PY
```

Interprete o resultado:

- `Existe: False`: collection nova; faca a primeira indexacao normalmente.
- `Existe: True` e `Pontos: 0`: collection vazia; a indexacao normal e segura.
- `Existe: True` e possui pontos: pare e decida se deseja manter ou substituir a base.

## 9. Primeira indexacao

Depois de validar os chunks e confirmar que a collection e nova ou vazia:

```bash
python pipeline.py
```

O pipeline regenera os chunks, gera os embeddings e envia os pontos ao Qdrant em lotes.

Os pontos recebem IDs determinísticos. Em modo `mirror`, a ordem é: validar chunks e manifesto, enviar pontos novos/alterados e só então remover IDs obsoletos. Se houver falha local ou no upsert, a limpeza não é executada.

Nao use `--only-chunks`, pois essa opcao interrompe o pipeline antes dos embeddings.

Nao use `--recreate` na primeira carga de uma collection nova.

### Configuracao Pinecone atual

A alternativa atual ao Qdrant usa o pacote oficial `langchain-pinecone`:

```yaml
embedding:
  provider: "openai"
  model: "text-embedding-3-small"
  dimensions: 1536
  batch_size: 50

vector_store:
  provider: "pinecone"
  index_name: "lead-media"
  namespace: "vivo_gold_banda_larga_pf"
```

No `.env`, mantenha:

```dotenv
PINECONE_API_KEY=...
```

No Pinecone:

- `lead-media` e o indice fisico;
- `vivo_gold_banda_larga_pf` e o namespace isolado desta base;
- o indice e o embedding usam 1536 dimensoes;
- os IDs sao determinísticos, portanto repetir um upsert dos mesmos chunks atualiza os registros em vez de criar novas copias;
- se documentos ou chunks forem removidos, use `--recreate` para eliminar registros antigos do namespace.

## 10. Confirmar a indexacao

Repita a consulta da secao 8. A quantidade de pontos deve normalmente ser igual ao total de chunks exibido pelo pipeline.

Exemplo:

```text
Total de chunks: 191
Pontos no Qdrant: 191
```

## 11. Atualizar uma base existente sem duplicar

Uma execucao comum em uma collection preenchida adiciona novos pontos e pode duplicar o conteudo.

Para substituir integralmente a base pelos documentos atuais da pasta:

1. confira cuidadosamente `vector_store.collection_name`;
2. gere e revise os chunks com `--only-chunks`;
3. execute:

```bash
python pipeline.py --recreate
```

No Qdrant, `--recreate` apaga somente a collection configurada, cria-a novamente e indexa a versao atual dos documentos.

No Pinecone, `--recreate` nao apaga o indice compartilhado. Ele limpa somente o namespace configurado e indexa a versao atual dos documentos.

Nunca use `--recreate` sem conferir o nome da collection, pois os dados anteriores daquela collection serao apagados.

## 12. Testar a busca

Apos indexar, consulte os chunks mais proximos:

```bash
python search.py "Quais sao os planos Vivo Fibra?"
```

Para retornar mais resultados:

```bash
python search.py --k 6 "Quais beneficios o cliente possui?"
```

Esse teste gera o embedding da pergunta e consulta a collection indicada no `config.yaml`.

## 13. Chat interativo

O projeto possui:

```bash
python chat.py
```

Entretanto, o texto e as mensagens do `chat.py` ainda estao escritos especificamente para C6 Empresas. Antes de usa-lo com a base Vivo, adapte o prompt do chatbot para o projeto atual. A busca com `search.py` ja usa a collection configurada e pode ser usada para validar a recuperacao.

## 14. Criar uma nova base

Para iniciar outro projeto sem misturar conteudo:

1. crie uma pasta exclusiva em `documentos/`;
2. coloque nela somente os `.md` daquela base;
3. altere `projeto.nome` e `projeto.descricao`;
4. altere todos os caminhos para uma pasta exclusiva em `output/`;
5. escolha um `collection_name` novo;
6. execute `python pipeline.py --only-chunks`;
7. revise o JSON;
8. confirme que a collection nao existe ou esta vazia;
9. execute `python pipeline.py` uma unica vez.

## 15. Problemas comuns

### O prompt mostra Python 3.12

Ative o ambiente:

```bash
source .venv/bin/activate
```

### `uv init` informa que o projeto ja existe

Isso e normal. Nao use `uv init`; o projeto ja possui `pyproject.toml`.

### Aviso `Failed to hardlink files`

O projeto esta em `/mnt/f` e o cache do `uv` esta no filesystem Linux. Use:

```bash
uv sync --python 3.14 --locked --link-mode=copy
```

### `load_dotenv()` falha em um script via stdin

Use o caminho explicito:

```python
load_dotenv(".env")
```

### Qdrant retorna `Connection refused`

Confirme no `.env`:

```dotenv
QDRANT_URL=https://qdrant.bigdates.com.br
```

O helper atual do projeto converte HTTPS sem porta para a porta 443. Nao acrescente `:6333` ao endpoint publico.

### A collection ja possui pontos

Nao execute o pipeline comum novamente. Se a intencao for substituir toda a base, revise o nome e use `--recreate`.

### Os documentos nao aparecem

Confirme que:

- possuem extensao `.md`;
- estao diretamente em `caminhos.input_dir`;
- nao estao apenas em uma subpasta;
- o caminho no YAML foi salvo corretamente.

## 16. Rotina recomendada

Para uma base nova:

```bash
source .venv/bin/activate
python pipeline.py --only-chunks
# revisar chunks.json e confirmar a collection
python pipeline.py
python search.py "pergunta de teste"
```

Para atualizar integralmente uma base existente:

```bash
source .venv/bin/activate
python pipeline.py --only-chunks
# revisar chunks.json e conferir cuidadosamente collection_name
python pipeline.py --recreate
python search.py "pergunta de teste"
```
