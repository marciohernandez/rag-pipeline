# Testes

<!-- specsfy:documentator:start -->
## Resumo

- Arquivos de teste: 10.
- Runner: não identificado.
- Scripts: não declarados.

| Arquivo |
| --- |
| frontend/src/features/auth/LoginForm.a11y.test.tsx |
| frontend/src/features/auth/LoginForm.test.tsx |
| frontend/src/features/bases/DataGridBases.a11y.test.tsx |
| frontend/src/features/bases/ExcluirBaseDialog.test.tsx |
| frontend/src/features/bases/UploadBaseSheet.test.tsx |
| frontend/src/features/execucoes/FormularioConsulta.a11y.test.tsx |
| frontend/src/features/execucoes/FormularioConsulta.test.tsx |
| frontend/src/features/execucoes/PainelProgresso.test.tsx |
| frontend/src/lib/api-client.test.ts |
| frontend/src/lib/api-proxy.test.ts |
<!-- specsfy:documentator:end -->

## Testes Python verificados

- Runner: Pytest, grupo `dev` de `pyproject.toml`.
- Arquivos próprios: 20.
- Casos observados durante o RED da SPEC-0007: 238 casos executados; os 221
  casos anteriores permaneceram aprovados e os 17 casos novos falharam pelos
  gates ainda ausentes.

| Arquivo | Casos | Cobertura principal |
| --- | --- | --- |
| `tests/test_vectorstore_conformance.py` | 26 | núcleo do contrato de vector store (`ensure_ready`, `list_ids`, `upsert`, `query`) em todos os adapters, com extensão `mirror` restrita a Qdrant e in-memory |
| `tests/test_safety.py` | 23 | guardas de opção destrutiva, modo, escopo e remoção nos entrypoints |
| `tests/test_quality_gate.py` | 27 | gate de qualidade: seis invariantes críticos, seis sinais, limiares derivados e configuráveis, relatório, resultado estruturado e CLI de diagnóstico |
| `tests/test_ci_gates.py` | 17 | dependência e configuração do Ruff, ausência de achados, workflow de CI, proteção de branch e fechamento documental da SPEC-0007 |
| `tests/test_provider_factory.py` | 17 | criação de cada provider pela mesma factory e erro local antes de qualquer cliente remoto |
| `tests/test_describe_scope_conformance.py` | 16 | `describe_scope` nos quatro backends, incluindo escopo ausente e dimensão declarada |
| `tests/test_validation.py` | 15 | validação de recuperação: preflight, conferência de identidade, roteiro de consultas, relatório, JSON e desfechos |
| `tests/test_safety_policy.py` | 14 | contrato unitário de `SyncSafetyPolicy` |
| `tests/test_chunker.py` | 14 | resumos de seção, limiar mínimo e IDs determinísticos |
| `tests/test_client_neutrality.py` | 14 | neutralidade da identidade operacional, configuração local ignorada e guardas estáticas sobre os entrypoints |
| `tests/test_characterization_providers.py` | 13 | comportamento observável da camada de providers, congelado durante o corte de `src/pipeline/embedder.py` |
| `tests/test_qdrant_sync.py` | 12 | upsert antes da limpeza e preservação dos dados remotos em falha |
| `tests/test_describe_scope_backends.py` | 6 | caracterização de `describe` nos backends reais, com SDK substituído por dublê e sem rede |
| `tests/test_status_gate.py` | 5 | bloqueio de indexação por status configurável |
| `tests/test_docs_safety.py` | 5 | material operacional publicado sem caminho destrutivo |
| `tests/test_provider_boundaries.py` | 4 | fronteira estática de imports: SDK de vector store e classes de embeddings somente em `src/pipeline/providers/` |
| `tests/test_loader.py` | 3 | hash de origem e falha rápida de documento inválido |
| `tests/test_embedding_conformance.py` | 3 | determinismo e dimensão do adapter fake de embeddings |
| `tests/test_validation_boundaries.py` | 2 | ausência dos protótipos de diagnóstico e de SDK de provider no código de validação |
| `tests/test_manifest.py` | 2 | contagens e rejeição de IDs duplicados |

`tests/_fakes_vectorstore.py` não é arquivo de casos: reúne os dublês
compartilhados pelas suítes de conformidade.

**Atualização (SPEC-0012, 2026-09-04)**: a suíte cresceu para **281 casos
aprovados** com a adição de quatro arquivos do backend de aplicação —
`tests/test_app_executions.py` (6), `tests/test_app_bases.py` (2),
`tests/test_app_auth.py` (3, um deles parametrizado em 6 endpoints) e
`tests/test_app_queries.py` (3) — cobrindo os 13 cenários de aceite AC-001 a
AC-013 da SPEC-0012. Diferente do restante da suíte, esses quatro arquivos
**exigem um PostgreSQL de teste real** acessível via `APP_DATABASE_URL`
(`tests/conftest.py` define o padrão
`postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test`);
nenhum outro teste do repositório importa `src.app` ou toca esse banco. Ver
`.specsfy/STACK.md` para como provisionar esse Postgres nesta máquina.

Nenhuma suíte exige rede. Destinos remotos e SDKs são substituídos por dublês
observáveis, o que permite provar garantias de somente leitura sem tocar no
Qdrant ou em provedores de embeddings.

Comandos reproduzíveis: `uv run pytest` e `uv run ruff check`. O Ruff 0.16.5
está fixado no grupo de desenvolvimento. O lint local, o contrato do workflow
e a execução remota estão verdes; a regressão completa passou no PR #2
(commit 4f9be0e e no commit de liberação) em 2026-09-03.

Ambiguidade encontrada e corrigida durante a comprovação remota (T024): o
runner do GitHub faz um checkout limpo, sem `config.yaml` (arquivo local,
listado em `.gitignore`). Os casos `test_ac_007_config_de_uso_fora_do_indice_do_git`
e `test_ac_008_exemplo_versionado_e_neutro` dependem desse arquivo e
quebravam a suíte completa em toda execução remota. O workflow agora inclui o
passo **Prepare local configuration**, que copia `config.example.yaml` para
`config.yaml` e substitui `collection_name`/`namespace` por valores
fabricados e não sensíveis, reproduzindo o passo de configuração inicial do
`README.md` sem expor dado de cliente.

## Proteção de branch e verificação obrigatória

O workflow `CI` publica o check estável `Ruff and Pytest`. A proteção da branch
`main` deve exigir esse nome exato; renomear o job exige atualizar também a
regra do repositório.

### Configurar

1. Publique a branch de fase e abra um pull request para `main`, para que o
   check `Ruff and Pytest` exista no histórico do repositório.
2. No GitHub, abra **Settings → Rules → Rulesets** e crie ou edite a regra que
   alcança a branch padrão `main`.
3. Ative **Require status checks to pass**, adicione `Ruff and Pytest` e deixe
   a regra ativa. Não adicione segredo ou variável do projeto ao workflow.
4. Reabra a regra como uma pessoa que não a configurou e confira `main`, o
   requisito de status e o nome exato do check.

### Comprovar bloqueio e liberação

1. No mesmo pull request, publique um commit de prova com um arquivo Python
   temporário contendo um import não usado. Aguarde a esteira reprovar no passo
   **Run Ruff**.
2. Confirme que o pull request reprovado mostra o merge bloqueado pelo check
   obrigatório `Ruff and Pytest`. Registre na SPEC-0007 o responsável, o número
   do PR, a URL ou identificador do run, a data e o estado observado.
3. Remova o arquivo temporário em um novo commit e publique a correção. Aguarde
   **Run Ruff** e **Run Pytest** passarem.
4. Confirme que o pull request aprovado fica liberado do impedimento desse
   check. Registre a segunda execução nos mesmos campos da SPEC-0007.

O ensaio não conclui o merge e não mantém o arquivo de prova; ele verifica
somente que a regra bloqueia o estado vermelho e libera o estado verde. Se a
conta não oferecer acesso administrativo ou rulesets, registre a dependência
como bloqueio em vez de declarar AC-010 ou AC-011 como aprovado.
