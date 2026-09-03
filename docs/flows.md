# Fluxos

<!-- specsfy:documentator:start -->
## Fluxo principal

```mermaid
flowchart LR
  Entrada --> Aplicação --> Saída
```

```mermaid
sequenceDiagram
  participant Cliente
  participant Aplicação
  Cliente->>Aplicação: requisição
```
<!-- specsfy:documentator:end -->

## Fluxo CLI verificado

```mermaid
sequenceDiagram
  actor Operador
  participant CLI as pipeline.py
  participant Loader as loader/chunker/identity
  participant Audit as chunks.json + manifesto
  participant Vector as Banco vetorial
  Operador->>CLI: executar com config.yaml
  CLI->>Loader: carregar documentos e excluir por status bloqueante
  Loader-->>CLI: chunks com IDs estáveis
  CLI->>Audit: exportar chunks e manifesto
  alt somente chunks
    CLI-->>Operador: resumo local
  else indexação
    CLI->>Vector: upsert dos pontos atuais
    Vector-->>CLI: confirmação
    CLI->>Vector: remover obsoletos do mesmo project_id
    CLI-->>Operador: contagens da execução
  end
```

Falhas de carga em modo estrito e falhas de upsert interrompem o fluxo. A
remoção de obsoletos no Qdrant somente ocorre depois de upsert bem-sucedido.

Antes de qualquer chamada remota, `src.safety.SyncSafetyPolicy` interrompe a
execução quando `--recreate` é solicitado, quando provider e modo são
incompatíveis ou quando o lote não forma um escopo lógico único. A remoção de
obsoletos exige confirmação prévia de todos os pontos esperados; sem essa
confirmação, o fluxo falha e preserva os dados remotos.

## Fluxo de validação verificado

`validate.py` é somente leitura: nenhum caminho de execução, inclusive os de
falha, envia escrita, remoção ou preparação ao destino. Ele nunca usa
`ensure_ready`, porque aquele caminho cria a coleção ausente no adapter Qdrant e
transformaria um escopo inexistente em base vazia aprovada.

```mermaid
flowchart TD
  A[Operador executa validate.py] --> B[Carregar config.yaml]
  B -->|ilegível| Z2[Código 2: não foi possível validar]
  B --> C[Validação local completa]
  C --> C1[Gabarito de caminhos.consultas_referencia]
  C --> C2[Escopo lógico de projeto.nome + tenant]
  C --> C3[Dimensão de embedding.dimensions]
  C --> C4[validacao.limiar_minimo quando há consulta sem_resposta]
  C1 & C2 & C3 & C4 -->|qualquer inválida| Z2
  C -->|tudo válido| D[Preflight por leitura: describe_scope]
  D -->|escopo ausente ou dimensão divergente| Z2
  D --> E[Carregar manifesto da mesma base]
  E --> F[Conferir chunk_id do manifesto contra o destino]
  F --> G[Executar o roteiro de consultas do gabarito]
  G --> H{Faltantes, órfãos ou consulta reprovada?}
  H -->|sim| Z1[Código 1: base reprovada]
  H -->|não| Z0[Código 0: base aprovada]
```

Ordem e garantias observadas em `src/validation.py`:

1. **Toda a validação local precede qualquer acesso remoto.** Configuração
   incompleta ou gabarito malformado encerram com código `2` sem que um adapter
   chegue a ser criado.
2. **O preflight é leitura pura.** `describe_scope` confere existência do escopo
   e compatibilidade com `embedding.dimensions`.
3. **A conferência de identidade exige igualdade estrita** entre o conjunto de
   `chunk_id` do manifesto e o devolvido pelo destino, relatando faltantes e
   órfãos separadamente.
4. **O roteiro de consultas roda mesmo com a conferência divergente**, de
   propósito: é leitura pura e o operador precisa do quadro completo para
   decidir o que corrigir, em vez de descobrir um problema por vez.
5. **Impedimento não é reprovação.** Código `2` significa que não foi possível
   validar; código `1` significa que a validação ocorreu e encontrou
   divergência.

Relatório, JSON e log não contêm credenciais, tokens nem URLs de destino. O
resultado estruturado é gravado em `output/<base>/validation-<run_id>.json`.
