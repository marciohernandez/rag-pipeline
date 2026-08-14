# Plano de Implementação — Chunks de Resumo e Sincronização com Qdrant

## Status do plano

- **Situação:** implementação e carga remota concluídas; validação no Flowise pendente.
- **Branch de trabalho:** `test/adicionar-testes`.
- **Coleção de destino:** `vivo_gold_banda_larga_pf`.
- **Responsável pela exclusão da coleção atual:** usuário.
- **Regra de segurança:** nenhuma escrita ou exclusão no Qdrant será feita antes da geração local, dos testes e da confirmação explícita do usuário.

### Execução atual

- Ambiente WSL/`uv` preparado com Python 3.12 em filesystem Linux.
- Geração local concluída: 208 chunks, sendo 191 `detail` e 17 `section_summary`.
- Manifesto local validado com 208 IDs únicos e 7 documentos.
- Suíte automatizada: 9 testes aprovados.
- Preflight remoto concluído antes da carga: a coleção `vivo_gold_banda_larga_pf` não existia no Qdrant.
- Nova coleção criada e carregada: 208 pontos, com 191 chunks detalhados e 17 resumos.
- Segunda sincronização idêntica: 0 pontos novos/alterados, confirmando ausência de duplicação.
- Busca ampla de planos: o `section_summary` foi recuperado na primeira posição.
- Próxima ação: validar a mesma configuração na interface do Flowise.

## 1. Objetivo

Evoluir o pipeline de ingestão para:

1. gerar chunks detalhados a partir dos documentos Markdown;
2. gerar automaticamente chunks de resumo para seções com várias subseções;
3. manter os resumos sempre sincronizados com os documentos de origem;
4. usar IDs determinísticos no Qdrant;
5. impedir duplicações e remover chunks obsoletos de maneira segura;
6. validar todo o conteúdo localmente antes de alterar o banco vetorial;
7. manter a solução genérica para outros projetos e documentos Markdown.

O processamento RAG e a geração da resposta final continuarão sendo responsabilidade do Flowise. Este projeto continuará responsável somente por carregamento, chunking, geração de embeddings e indexação/sincronização no banco vetorial escolhido.

## 2. Estado atual conhecido

- O pipeline lê arquivos `.md` diretamente de `caminhos.input_dir`.
- A leitura atual não percorre subpastas.
- A estratégia configurada usa headings Markdown (`#`, `##` e `###`).
- O Qdrant está acessível em `qdrant.smartsystem.ia.br`.
- A coleção atual contém 191 pontos.
- A coleção configurada é `vivo_gold_banda_larga_pf`.
- O modelo de embedding é `text-embedding-3-small`.
- A dimensão configurada é 1536.
- A distância usada no Qdrant é cosseno.
- O `config.yaml` está configurado com `vector_store.provider: "qdrant"`.
- O ambiente será executado no WSL usando `uv`.
- A `.venv` atual está incompleta e precisará ser preparada antes dos testes.
- O indexador Qdrant atual não fornece IDs determinísticos ao adicionar documentos.
- Uma nova execução sem recriar a coleção pode duplicar os pontos atuais.
- O `upsert_from_chunks.py` atual envia todo o conteúdo de `chunks.json`.
- O tratamento atual de erros de chunking continua a execução quando um documento falha; esse comportamento não é seguro para sincronização em modo espelho.

## 3. Decisões confirmadas

### 3.1 Abrangência dos documentos

- Processar somente arquivos `.md` diretamente na pasta configurada.
- Não percorrer subpastas nesta implementação.
- Não adicionar suporte a PDF, DOCX ou outros formatos neste escopo.
- Aplicar a geração de resumos a qualquer Markdown elegível, sem regras específicas da Vivo.

### 3.2 Regra para geração de resumo

- Gerar um `section_summary` quando uma seção `##` tiver pelo menos três subseções `###` distintas.
- Incluir no resumo somente os títulos das subseções.
- Preservar a ordem em que as subseções aparecem no documento.
- Remover títulos duplicados.
- Não alterar os arquivos Markdown originais.
- Não criar arquivos `.md` de resumo mantidos manualmente.
- Gerar os resumos novamente em toda execução, usando o estado atual dos documentos.

### 3.3 Comportamento esperado após mudanças

- Subseção adicionada: incluir o título no resumo.
- Subseção renomeada: atualizar o título no resumo.
- Subseção removida: remover o título do resumo.
- Seção reduzida para menos de três subseções: remover seu `section_summary`.
- Documento adicionado: adicionar seus chunks detalhados e resumos.
- Documento alterado: atualizar seus chunks e resumos.
- Documento removido: remover do Qdrant todos os chunks associados a ele, quando o modo espelho estiver habilitado.
- Documento inalterado: evitar a geração e o envio desnecessários de novos embeddings quando a otimização por hash estiver ativa.

## 4. Formato proposto para o chunk de resumo

Exemplo:

```text
[Vivo Fibra PF - Ofertas Nacionais - Julho 2026 > Planos Vivo Fibra]

Itens disponíveis nesta seção:
- Vivo Fibra 500 MEGA
- Vivo Fibra 600 MEGA
- Vivo Fibra 700 MEGA
- Vivo Fibra 1 GIGA
- Vivo Fibra 2 GIGA
- Vivo Fibra 10 GIGA
```

Metadados mínimos previstos:

```json
{
  "chunk_type": "section_summary",
  "titulo": "Vivo Fibra PF - Ofertas Nacionais - Julho 2026",
  "secao": "Planos Vivo Fibra",
  "summary_child_count": 6,
  "nome_arquivo": "vivo_fibra_pf_julho_2026.md",
  "caminho_relativo": "vivo_gold_banda_larga_pf/vivo_fibra_pf_julho_2026.md",
  "breadcrumb": "[Vivo Fibra PF - Ofertas Nacionais - Julho 2026 > Planos Vivo Fibra]",
  "document_id": "<identificador estável do documento>",
  "source_hash": "<hash do conteúdo de origem>"
}
```

Os chunks detalhados continuarão sendo gerados normalmente e receberão `chunk_type: "detail"`.

## 5. Configuração prevista

Adicionar opções genéricas ao bloco `chunking` do `config.yaml`:

```yaml
chunking:
  generate_section_summaries: true
  section_summary_min_children: 3
```

Adicionar uma configuração explícita para sincronização. O nome definitivo será decidido durante a implementação, mantendo comportamento seguro por padrão. Exemplo conceitual:

```yaml
vector_store:
  sync_mode: "mirror"
```

O modo `mirror` significa que a pasta configurada é a fonte de verdade. Pontos associados a documentos ou chunks que não existem mais poderão ser removidos somente depois da validação completa da nova execução.

## 6. Identidade e idempotência

### 6.1 Metadados de identidade

Cada chunk deverá ter:

- `project_id`: identifica o projeto/base;
- `document_id`: identifica de maneira estável o arquivo de origem;
- `chunk_id`: identifica de maneira estável o chunk;
- `chunk_type`: `detail` ou `section_summary`;
- `source_hash`: hash do conteúdo atual do documento;
- `run_id`: identifica a execução que gerou o manifesto.

### 6.2 IDs determinísticos

- Usar um UUID determinístico compatível com o Qdrant.
- A identidade deverá considerar projeto, documento, tipo de chunk e posição/estrutura lógica.
- Executar novamente a mesma carga deverá atualizar os mesmos pontos.
- Um upsert repetido não poderá aumentar a contagem da coleção.

### 6.3 Pontos obsoletos

Depois que os novos pontos forem enviados com sucesso:

1. consultar os IDs existentes relacionados ao projeto/documento;
2. comparar com os IDs do manifesto validado;
3. calcular `IDs existentes - IDs esperados`;
4. remover somente essa diferença;
5. confirmar a contagem final.

Os pontos antigos não serão removidos antes da confirmação do upsert dos novos pontos.

## 7. Manifesto e segurança da sincronização

Antes de qualquer escrita remota, o pipeline deverá produzir um manifesto local contendo, no mínimo:

- `run_id`;
- projeto;
- coleção;
- modelo e dimensão do embedding;
- lista de documentos processados;
- hashes dos documentos;
- quantidade de chunks detalhados;
- quantidade de resumos;
- IDs esperados;
- erros encontrados;
- data da geração.

### Regra de fail-fast

Se qualquer documento falhar durante carregamento, parsing, chunking, geração de resumo ou validação:

- abortar a execução completa;
- não fazer upsert;
- não remover pontos;
- apresentar os erros ao usuário;
- preservar a coleção remota no estado anterior.

## 8. Plano detalhado de tarefas

### Fase 1 — Linha de base e ambiente

- [ ] Confirmar branch e estado do Git.
- [ ] Preservar alterações não relacionadas existentes.
- [ ] Confirmar que `.env` não é rastreado pelo Git.
- [ ] Preparar `uv` no WSL.
- [ ] Recriar o ambiente virtual do projeto de forma controlada.
- [ ] Instalar/sincronizar dependências pelo `uv.lock`.
- [ ] Registrar versões de Python, `uv`, Qdrant client e bibliotecas LangChain.
- [ ] Gerar os chunks atuais sem indexar.
- [ ] Registrar contagem e estrutura atuais como linha de base.

**Critério de saída:** ambiente reproduzível e linha de base registrada sem escrita no Qdrant.

### Fase 2 — Configuração e geração de resumos

- [ ] Adicionar as configurações de resumo ao `config.yaml`.
- [ ] Implementar função pura para agrupar subseções por documento/título/seção.
- [ ] Preservar a ordem original das subseções.
- [ ] Remover títulos duplicados.
- [ ] Aplicar o limite mínimo de três subseções.
- [ ] Criar o texto padronizado do resumo.
- [ ] Adicionar os metadados do `section_summary`.
- [ ] Marcar chunks normais como `detail`.
- [ ] Integrar os resumos ao resultado de `chunk_documents`.
- [ ] Garantir que o conteúdo não exceda os limites configurados.

**Critério de saída:** o resumo dos planos é produzido automaticamente com os seis títulos corretos e os chunks detalhados permanecem disponíveis.

### Fase 3 — IDs, hashes e manifesto

- [ ] Definir `project_id` e `document_id`.
- [ ] Implementar hash estável do documento.
- [ ] Implementar UUIDs determinísticos para chunks detalhados.
- [ ] Implementar UUIDs determinísticos para resumos.
- [ ] Criar o manifesto de execução.
- [ ] Validar unicidade dos IDs antes do upsert.
- [ ] Tornar a exportação local resistente a arquivo parcial.
- [ ] Alterar o tratamento de erros para fail-fast em sincronizações.

**Critério de saída:** duas gerações idênticas produzem os mesmos IDs e o mesmo manifesto lógico.

### Fase 4 — Sincronização segura com Qdrant

- [ ] Passar IDs explícitos ao Qdrant durante o upsert.
- [ ] Implementar consulta dos pontos existentes por projeto/documento.
- [ ] Implementar comparação entre IDs existentes e esperados.
- [ ] Fazer upsert antes de remover IDs obsoletos.
- [ ] Remover somente IDs comprovadamente obsoletos.
- [ ] Tratar documentos removidos no modo espelho.
- [ ] Garantir que um erro de rede não execute a etapa de limpeza.
- [ ] Registrar contagens antes e depois.
- [ ] Garantir que a operação normal não apague a coleção inteira.

**Critério de saída:** uma segunda sincronização idêntica não cria duplicações, e alterações/remoções controladas não deixam pontos obsoletos.

### Fase 5 — Testes automatizados

- [ ] Configurar `pytest` como dependência de desenvolvimento.
- [ ] Testar seção com exatamente três subseções.
- [ ] Testar seção com menos de três subseções.
- [ ] Testar múltiplas seções no mesmo documento.
- [ ] Testar títulos duplicados.
- [ ] Testar preservação da ordem.
- [ ] Testar documento sem headings elegíveis.
- [ ] Testar inclusão de uma subseção.
- [ ] Testar renomeação de uma subseção.
- [ ] Testar exclusão de uma subseção.
- [ ] Testar remoção do resumo quando a seção ficar abaixo do limite.
- [ ] Testar adição, alteração e exclusão de documentos.
- [ ] Testar estabilidade e unicidade dos IDs.
- [ ] Testar reexecução sem duplicação.
- [ ] Testar que erro local impede qualquer escrita remota.
- [ ] Testar que falha no upsert impede a limpeza de pontos antigos.
- [ ] Testar o comportamento atual dos chunks detalhados para evitar regressões.

**Critério de saída:** suíte completa aprovada no WSL.

### Fase 6 — Validação local completa

- [ ] Executar o pipeline em modo `--only-chunks`.
- [ ] Revisar o `chunks.json` gerado.
- [ ] Revisar o manifesto.
- [ ] Confirmar o resumo com os seis planos.
- [ ] Verificar quantidade de resumos por documento.
- [ ] Verificar tamanhos e metadados.
- [ ] Verificar IDs duplicados.
- [ ] Confirmar ausência de erros de carregamento/chunking.
- [ ] Executar `git diff --check`.
- [ ] Executar toda a suíte de testes novamente.

**Critério de saída:** conjunto local completo, auditado e pronto para indexação.

### Fase 7 — Preflight remoto e ponto de confirmação

- [ ] Consultar o Qdrant somente para leitura.
- [ ] Confirmar host, autenticação, dimensão e distância.
- [ ] Registrar o estado da coleção atual.
- [ ] Recomendar/confirmar snapshot antes da exclusão.
- [ ] Aguardar o usuário excluir a coleção antiga.
- [ ] Receber confirmação explícita do usuário.
- [ ] Confirmar por leitura que a coleção não existe.

**Bloqueio obrigatório:** nenhuma carga será iniciada antes da confirmação explícita da exclusão pelo usuário.

### Fase 8 — Nova carga

- [ ] Criar `vivo_gold_banda_larga_pf` com 1536 dimensões e distância cosseno.
- [ ] Enviar os chunks validados em lotes.
- [ ] Não usar exclusão automática da coleção.
- [ ] Interromper sem limpeza se qualquer lote falhar.
- [ ] Confirmar a quantidade final de pontos.
- [ ] Confirmar que a quantidade remota corresponde ao manifesto.
- [ ] Verificar amostras de `detail` e `section_summary`.
- [ ] Verificar unicidade dos IDs.

**Critério de saída:** coleção nova completa e consistente com o manifesto local.

### Fase 9 — Validação de recuperação

- [ ] Pesquisar `Quais são os Planos disponíveis?`.
- [ ] Confirmar que o `section_summary` dos planos aparece entre os primeiros resultados.
- [ ] Pesquisar `Qual o preço do Vivo Fibra 500 Mega?`.
- [ ] Pesquisar `Como ganhar Vale Bônus?`.
- [ ] Testar uma pergunta sem resposta na base.
- [ ] Validar os resultados no Flowise com o `Top K` usado em produção.
- [ ] Confirmar que perguntas amplas e específicas continuam funcionando.

**Critério de saída:** recuperação aprovada no Qdrant e no Flowise.

### Fase 10 — Documentação e entrega

- [ ] Atualizar README e guia de uso.
- [ ] Documentar as opções de resumo.
- [ ] Documentar IDs determinísticos e modo espelho.
- [ ] Documentar carga completa e atualização incremental.
- [ ] Documentar tratamento de documentos removidos.
- [ ] Documentar comandos WSL/`uv`.
- [ ] Documentar preflight, rollback e recuperação de falhas.
- [ ] Registrar contagens e resultados finais.
- [ ] Revisar alterações da branch antes de qualquer commit/publicação.

## 9. Critérios globais de aceite

A implementação será considerada concluída somente se:

1. os Markdown originais não precisarem de resumos manuais;
2. o resumo dos planos contiver os seis planos atuais;
3. mudanças nos headings atualizarem automaticamente o resumo;
4. a remoção de headings ou documentos não deixar pontos obsoletos;
5. uma execução repetida não aumentar indevidamente a contagem;
6. falhas locais ou remotas não causarem limpeza parcial;
7. todos os testes forem aprovados no WSL;
8. a contagem remota corresponder ao manifesto;
9. a pergunta ampla sobre planos recuperar o resumo;
10. o Flowise continuar recuperando chunks detalhados para perguntas específicas;
11. o procedimento estiver documentado e reproduzível.

## 10. Rollback e recuperação

Antes da exclusão da coleção atual, deverá existir pelo menos uma forma validada de recuperação:

- snapshot do Qdrant; ou
- documentos originais, configuração, versão anterior do código e chunks exportados suficientes para reconstrução.

Se a nova carga falhar antes de ser concluída:

1. não executar limpeza adicional;
2. preservar logs, manifesto e erro do lote;
3. corrigir a causa localmente;
4. repetir a carga usando os mesmos IDs determinísticos; ou
5. restaurar o snapshot, caso necessário.

## 11. Fora do escopo inicial

- Alterar a lógica interna do Flowise.
- Gerar respostas com LLM neste pipeline.
- Criar resumos com LLM.
- Processar subpastas recursivamente.
- Processar PDF, DOCX, HTML ou outros formatos.
- Editar automaticamente o conteúdo dos documentos Markdown.
- Publicar, fazer commit, push ou abrir pull request sem solicitação explícita.

## 12. Autorização para início

Este documento registra somente o plano. A execução deverá começar apenas após uma nova autorização explícita do usuário.
