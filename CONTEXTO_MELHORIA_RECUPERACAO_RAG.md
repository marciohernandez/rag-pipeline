# Contexto para melhoria da recuperação RAG

## Objetivo

Este documento registra o estado atual de um pipeline RAG, um problema de recuperação observado em teste real e possíveis soluções. Ele foi preparado para fornecer contexto suficiente a outro modelo ou desenvolvedor sem depender do histórico anterior da conversa.

## 1. Estado atual do projeto

O projeto é um pipeline Python que:

1. carrega documentos Markdown;
2. extrai frontmatter YAML como metadados;
3. divide documentos em chunks;
4. exporta os chunks para auditoria em JSON;
5. gera embeddings com OpenAI;
6. envia vetores para Pinecone;
7. permite busca semântica nos documentos indexados.

Tecnologias principais:

- Python 3.14;
- LangChain v1+;
- `langchain-pinecone==0.2.13`;
- `pinecone==7.3.0`;
- `langchain-openai`;
- modelo `text-embedding-3-small`;
- vetores com 1536 dimensões.

Configuração Pinecone:

```text
Índice: lead-media
Dimensão: 1536
Métrica: cosine
Namespace: vivo_gold_banda_larga_pf
Quantidade de vetores: 191
```

O índice físico é compartilhado, mas a base está isolada pelo namespace `vivo_gold_banda_larga_pf`.

Os sete documentos da base estão em:

```text
documentos/vivo_gold_banda_larga_pf/
```

Eles contêm informações sobre planos, ofertas, benefícios, serviços adicionais, termos, categorias de clientes e regulamentos Vivo Fibra PF.

## 2. Estratégia atual de chunking

```yaml
chunking:
  default_chunk_size: 1000
  default_chunk_overlap: 200
  default_splitter: "header"

  headers_to_split_on:
    - ["#", "titulo"]
    - ["##", "secao"]
    - ["###", "subsecao"]
```

Funcionamento:

- `#` gera `titulo`;
- `##` gera `secao`;
- `###` gera `subsecao`;
- se uma seção ultrapassar 1.000 caracteres, ela é subdividida recursivamente;
- o breadcrumb é injetado no início do texto do chunk.

Exemplo:

```text
[Vivo Fibra PF - Ofertas Nacionais - Julho 2026 > Planos Vivo Fibra > Vivo Fibra 500 MEGA]
```

Cada chunk recebe automaticamente:

- `nome_arquivo`;
- `caminho_relativo`;
- `titulo`;
- `secao`;
- `subsecao`;
- `breadcrumb`;
- `chunk_index`;
- `total_chunks`.

## 3. Estrutura que apresentou o problema

O documento de planos está organizado aproximadamente assim:

```markdown
# Vivo Fibra PF - Ofertas Nacionais - Julho 2026

## Planos Vivo Fibra

### Vivo Fibra 500 MEGA
Detalhes, preço, upload, benefícios e opcionais.

### Vivo Fibra 600 MEGA
Detalhes, preço, upload, benefícios e opcionais.

### Vivo Fibra 700 MEGA
Detalhes, preço, upload, benefícios e opcionais.

### Vivo Fibra 1 GIGA
Detalhes, preço, upload, benefícios e opcionais.

### Vivo Fibra 2 GIGA
Detalhes, preço, upload, benefícios e opcionais.

### Vivo Fibra 10 GIGA
Detalhes, preço, upload, benefícios e opcionais.
```

Como o splitter reconhece `###`, cada plano foi transformado em um chunk detalhado separado.

## 4. Teste realizado

Um agente consultou a ferramenta de busca com a entrada:

```text
Planos Vivo Fibra disponíveis para cliente Pessoa Física contratado pela Gold: velocidades, valores e condições
```

A busca retornou quatro chunks:

1. Vivo Fibra 10 GIGA;
2. Vivo Fibra 1 GIGA;
3. Vivo Fibra 500 MEGA;
4. Vivo Fibra 2 GIGA.

Os chunks estavam semanticamente corretos e continham preço, download, upload, benefícios, opcionais, disponibilidade e origem.

Entretanto, a resposta ficou incompleta. Ficaram ausentes pelo menos:

- Vivo Fibra 600 MEGA;
- Vivo Fibra 700 MEGA.

## 5. Diagnóstico

O problema não é conexão, embedding, Pinecone, namespace ou ausência dos documentos.

O problema é de cobertura, ou recall, para perguntas abrangentes.

A busca vetorial retorna os `k` chunks mais próximos. A ferramenta aparentemente usa `k=4`. Como cada plano está em um chunk separado, uma pergunta solicitando todos os planos exige mais de quatro resultados relevantes.

Resumo do comportamento:

```text
Pergunta específica + chunk específico = boa precisão

Pergunta abrangente + itens em vários chunks + top_k baixo
= resposta parcial
```

A busca por similaridade não garante automaticamente que todos os elementos de uma lista foram recuperados.

## 6. O split em `###` está errado?

Não necessariamente.

Um plano por `###` funciona bem para perguntas como:

```text
Quanto custa o Vivo Fibra 600 Mega?
```

Remover `###` não resolveria o problema de forma confiável. A seção inteira de planos ultrapassaria 1.000 caracteres e seria dividida pelo splitter recursivo em pontos menos previsíveis, podendo separar nome, preço, condições e benefícios.

Portanto, a granularidade detalhada deve ser preservada.

## 7. Solução principal: representação em dois níveis

Manter duas representações do mesmo conteúdo:

```text
Documento
├── chunk de resumo ou catálogo
└── chunks detalhados de cada item
```

Exemplo:

```markdown
## Resumo de todos os planos Vivo Fibra PF

| Plano | Preço base | Download | Upload |
|---|---:|---:|---:|
| Vivo Fibra 500 Mega | R$ 100,00/mês | 500 Mbps | 250 Mbps |
| Vivo Fibra 600 Mega | R$ 120,00/mês | 600 Mbps | 300 Mbps |
| Vivo Fibra 700 Mega | R$ 150,00/mês | 700 Mbps | 350 Mbps |
| Vivo Fibra 1 Giga | R$ 300,00/mês | 1 Gbps | 500 Mbps |
| Vivo Fibra 2 Giga | R$ 400,00/mês | 2 Gbps | 1 Gbps |
| Vivo Fibra 10 Giga | R$ 2.000,00/mês | 10 Gbps | 5 Gbps |

Os valores e a disponibilidade devem ser confirmados conforme cobertura e vigência.

## Planos Vivo Fibra

### Vivo Fibra 500 MEGA
Detalhes completos...

### Vivo Fibra 600 MEGA
Detalhes completos...
```

Assim:

- perguntas amplas recuperam o resumo;
- perguntas específicas recuperam o detalhe;
- o `###` continua útil;
- não é necessário criar um chunk enorme com todos os detalhes.

## 8. Metadados sugeridos

Resumo:

```json
{
  "documento_id": "vivo-fibra-pf-ofertas-2026-07",
  "chunk_type": "summary",
  "categoria": "planos",
  "produto": "Vivo Fibra",
  "publico": "Pessoa Fisica",
  "status": "vigente"
}
```

Detalhe:

```json
{
  "documento_id": "vivo-fibra-pf-ofertas-2026-07",
  "chunk_type": "detail",
  "item_id": "vivo-fibra-600-mega",
  "categoria": "planos",
  "produto": "Vivo Fibra",
  "publico": "Pessoa Fisica",
  "status": "vigente"
}
```

Metadados ajudam em filtros e auditoria, mas termos importantes também devem aparecer nos headings ou no texto, pois o embedding é gerado principalmente a partir do `page_content`.

## 9. Melhorias adicionais na recuperação

### Aumentar `top_k`

Elevar `top_k` de 4 para 8 ou 10 melhora a cobertura, mas não garante uma lista completa. Os resultados continuam ordenados por similaridade, não por completude.

### Recuperação em duas etapas

```text
Pergunta
  -> recuperar 10 a 20 candidatos
  -> aplicar reranking
  -> selecionar 4 a 8 chunks finais
  -> gerar a resposta
```

### Reconhecer perguntas exaustivas

O agente deve reconhecer expressões como:

- todos;
- quais são os planos;
- liste as opções;
- benefícios disponíveis;
- compare todas as ofertas.

Nesses casos, deve:

1. procurar chunks `summary`;
2. aumentar a recuperação;
3. agrupar por documento ou categoria;
4. executar busca complementar, se necessário;
5. não afirmar completude sem evidência.

### Expandir chunks relacionados

Quando uma pergunta for abrangente, recuperar um resultado e depois buscar chunks irmãos com o mesmo `documento_id`, `secao` ou `categoria`.

## 10. Problema adicional no agente

O resultado foi apresentado no formato bruto da ferramenta:

```json
{
  "tool": "search_vivo_broadband_support_knowledge",
  "toolInput": {"input": "..."},
  "toolOutput": "..."
}
```

Se isso foi mostrado ao usuário final, existe um problema de apresentação. O agente deveria usar o `toolOutput` internamente e produzir uma resposta amigável, preferencialmente uma tabela, sem expor o JSON da ferramenta.

Instrução sugerida para o agente:

```text
Quando a pergunta solicitar todos os planos, opções, benefícios ou itens:

1. Procure primeiro um resumo consolidado.
2. Se os resultados parecerem parciais, faça uma busca complementar.
3. Não afirme que a lista está completa sem evidência.
4. Organize comparações em tabela.
5. Não exponha chamadas ou JSON bruto de ferramentas.
6. Use somente informações da base.
7. Informe fonte, vigência e restrições relevantes.
```

## 11. Como lidar com muitos documentos e formatos

Não é viável revisar manualmente todos os chunks. O pipeline deve automatizar a qualidade:

```text
Arquivos originais
  -> extração para Markdown
  -> normalização estrutural
  -> enriquecimento de metadados
  -> classificação do conteúdo
  -> chunks summary + detail
  -> relatório de qualidade
  -> avaliações automáticas
  -> indexação
```

Ao converter PDF, DOCX, HTML, planilhas ou imagens, preservar:

- arquivo original;
- página;
- seção;
- tabela de origem;
- URL ou fonte;
- data de extração;
- data de atualização;
- vigência;
- versão;
- status.

Classificar seções antes do chunking:

- FAQ: uma pergunta e resposta por chunk;
- procedimento: passos completos juntos;
- catálogo: resumo completo e um chunk por item;
- tabela: preservar a tabela e gerar resumo textual;
- regulamento: dividir por cláusula ou assunto;
- oferta: preservar valores, público, vigência e restrições.

## 12. Validações automáticas sugeridas

Antes da indexação, gerar alertas como:

```text
AVISO: seção "Planos Vivo Fibra" possui 6 subseções,
mas não possui um chunk de resumo.
```

```text
AVISO: 38 chunks possuem menos de 250 caracteres.
```

```text
AVISO: documento sem produto, público, fonte ou data de atualização.
```

```text
AVISO: heading genérico "Preço" pode perder contexto isoladamente.
```

Também verificar:

- chunks grandes ou pequenos demais;
- tabelas divididas;
- metadados ausentes;
- conteúdo duplicado;
- versões vencidas e vigentes misturadas;
- conflitos de preço, prazo ou condição;
- caracteres corrompidos por OCR ou conversão.

## 13. Avaliações automáticas

Criar perguntas de referência para cada base:

```yaml
- pergunta: "Quais são todos os planos Vivo Fibra?"
  deve_conter:
    - "500 Mega"
    - "600 Mega"
    - "700 Mega"
    - "1 Giga"
    - "2 Giga"
    - "10 Giga"

- pergunta: "Quanto custa o Vivo Fibra 600 Mega?"
  deve_conter:
    - "R$ 120,00"

- pergunta: "Quem tem desconto no Cinemark?"
  documento_esperado: "regulamento-cinemark-vivo-valoriza-2025.md"
```

Após cada alteração, medir:

- recuperação do documento correto;
- presença dos fatos esperados;
- cobertura de listas;
- ausência de fatos inventados;
- respeito a vigência e público;
- qualidade das fontes retornadas.

## 14. Atualização no Pinecone

O projeto usa IDs determinísticos derivados de:

```text
namespace + caminho_relativo + chunk_index
```

Consequências:

- repetir o pipeline com os mesmos chunks atualiza os mesmos IDs;
- a repetição não cria cópias;
- se chunks forem removidos ou reordenados, podem permanecer registros antigos;
- a recuperação normal consiste em validar chunks e manifesto e repetir o pipeline em modo incremental.

No Pinecone, a sincronização incremental não remove automaticamente registros que
deixaram de existir na origem. Uma limpeza administrativa exige um fluxo próprio,
fora da rotina normal deste pipeline.

## 15. Proposta em etapas

### Etapa 1 — correção imediata

1. manter o split em `#`, `##` e `###`;
2. adicionar um resumo consolidado ao documento de planos;
3. elevar `top_k` para 8 ou 10;
4. impedir exposição do JSON bruto da ferramenta;
5. validar o manifesto e reindexar com `python pipeline.py`;
6. testar perguntas gerais e específicas.

### Etapa 2 — melhoria estrutural

1. adicionar `documento_id`, `chunk_type`, `item_id`, `status` e vigência;
2. detectar automaticamente catálogos, listas e tabelas;
3. produzir chunks `summary` e `detail`;
4. gerar relatório de qualidade;
5. validar metadados mínimos.

### Etapa 3 — recuperação avançada

1. recuperar mais candidatos;
2. adicionar reranking;
3. reconhecer perguntas exaustivas;
4. expandir chunks irmãos;
5. criar avaliações automáticas de recall e completude.

## 16. Decisões para discussão

O próximo modelo deve ajudar a decidir:

1. Os resumos devem ser escritos na normalização do Markdown ou gerados pelo pipeline?
2. Como identificar listas e catálogos com segurança durante a ingestão?
3. É melhor indexar `summary` e `detail` no mesmo namespace?
4. Como implementar expansão por `documento_id` e `secao` usando Pinecone e LangChain v1+?
5. Qual reranker usar e em qual etapa?
6. Como estruturar o relatório de qualidade dos chunks?
7. Como criar avaliações reaproveitáveis entre bases?
8. Como impedir uso de conteúdo expirado quando há uma versão vigente?

## 17. Resultado esperado

```text
Pergunta específica:
"Quanto custa o Vivo Fibra 600 Mega?"
-> recuperar o chunk detalhado do plano.
```

```text
Pergunta abrangente:
"Quais são todos os planos Vivo Fibra disponíveis?"
-> recuperar um resumo completo ou reunir todos os chunks relacionados,
sem omitir planos e sem afirmar completude indevida.
```

O objetivo final é reduzir revisão manual e melhorar precisão, cobertura, auditabilidade e manutenção da base.
