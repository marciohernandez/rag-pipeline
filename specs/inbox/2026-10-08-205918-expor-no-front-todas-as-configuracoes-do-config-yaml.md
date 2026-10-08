# Inbox: Expor no front todas as configurações do config.yaml

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T20:59:18Z |
| Slug | expor-no-front-todas-as-configuracoes-do-config-yaml |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `615f9bcc1ce6fc82bd01e5e7063ef3ce875b7a7a863c9ff53654425cbf25691f` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

eu preciso que esteja tudo no front [...] todas as configuração que faço para definir todo o processamento até subir, escolher nome de coleção etc eu preciso que eu tenha a opção de definir no front. [...] eu quero fazer agora esse parte de expor no front todas as configurações do .ymal

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Pessoa operadora quer definir pelo front todas as configurações do processamento hoje presentes no config.yaml, do chunking à publicação no Qdrant.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Parte das configurações do pipeline só existe no config.yaml (resumos de seção, headers de divisão, qualidade mínima, status bloqueado, parâmetros de embedding), então ajustá-las exige editar arquivo e reiniciar, fora do front.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que opera o pipeline pela interface (owner/admin) e testa o processamento real.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Definir todo o processamento, do arquivo até a coleção no Qdrant, pelo front, sem editar config.yaml.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: tudo que define o processamento até subir, inclusive o nome da coleção, deve ser definível no front. Declaração: quer fazer isso agora. Inferência: o SPEC-0026 já entregou splitter, tamanho, overlap, conexões e coleção; sobram as demais seções do config.yaml. Fora de escopo declarado na SPEC-0026: tela global de configurações, outros formatos e providers.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível persistência por Base dos parâmetros adicionais (SPEC-0026 já guarda splitter, tamanho, overlap e vínculos); a revisar se algum valor é global ou por Base.

### Riscos e dependências

**Análise preliminar:** Config global do servidor versus configuração por Base; compatibilidade com Bases anteriores; validação de limites; segredos continuam só nas conexões cifradas; a SPEC-0026 deixou itens explicitamente fora de escopo.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog novo para expor as seções restantes do config.yaml no fluxo de Nova Base; avaliar também tela de padrões do projeto. Relacionado a SPEC-0026, SPEC-0019 e BACKLOG-0035 (apagar Base usa a coleção da Base).

## Pontos a revisar no futuro

**A revisar:** Quais chaves do config.yaml entram (chunking.headers_to_split_on, generate_section_summaries, section_summary_min_children, qualidade.minimo_util, contrato_markdown.status_bloqueado, embedding.*, vector_store.*, caminhos); onde configurar (por Base ou global); quem pode alterar; o que fazer com o frontmatter por arquivo; ordem em relação ao bug 0035.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
