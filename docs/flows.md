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
  CLI->>Loader: carregar e preparar documentos
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
