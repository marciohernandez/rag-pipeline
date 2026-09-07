# Frontend demonstrável (SPEC-0013)

Interface web da fatia funcional do `rag-pipeline`: login por token de
demonstração, listagem das bases do tenant/projeto ativo, envio de base
(upload `.md` ou base preparada), acompanhamento da execução assíncrona com
polling, repetição de execução falhada, exclusão de base e consulta à base
indexada com os chunks-fontes.

Projeto Node autocontido (DEC-001): `package.json`, `tsconfig.json` e
`components.json` próprios, sem se misturar ao tooling `uv` da raiz.

Stack: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui sobre
Base UI, Vitest + Testing Library.

## Pré-requisitos

O frontend não funciona sozinho — ele consome o backend FastAPI de `src/app/`.
Antes de subir aqui, deixe rodando, a partir da **raiz do repositório**:

```bash
# 1. PostgreSQL de teste
docker compose up -d postgres-test

# 2. Schema da aplicação e da fila (uma vez por banco novo)
uv run alembic upgrade head
uv run python -m procrastinate --app src.app.worker.app schema --apply

# 3. API
uv run uvicorn src.app.main:app --port 8000

# 4. Worker (processo separado; sem ele a execução fica presa em `pending`)
uv run python -m procrastinate --app src.app.worker.app worker
```

Consulte o `README.md` da raiz para as variáveis `APP_*` (banco, embeddings,
vector store, storage).

## Rodar

```bash
npm ci
cp .env.example .env.local   # ajuste API_PROXY_TARGET se a API não estiver em :8000
npm run dev
```

Abra <http://localhost:3000> e entre com um token de demonstração
(`token-demo-owner`, `token-demo-admin`, `token-demo-member` ou
`token-demo-outro-tenant` — ver `src/app/main.py`).

### Como o frontend fala com a API

O navegador **só** fala com a origem do Next. `next.config.ts` reencaminha
`/api/*` para `API_PROXY_TARGET` no servidor, então tudo fica em mesma origem.

Isso é deliberado e necessário: o backend não tem `CORSMiddleware`, de modo que
o preflight `OPTIONS` — exigido pelo cabeçalho `Authorization` — responderia
`405`; e a CSP declarada em `next.config.ts` não tem `connect-src`, caindo em
`default-src 'self'`, o que já bloquearia qualquer `fetch` cross-origin.

Apontar o navegador direto para outra origem (preenchendo
`NEXT_PUBLIC_API_BASE_URL`) exigiria **as duas** mudanças: CORS no backend e
`connect-src` na CSP.

## Verificação

```bash
npm run lint       # ESLint
npm run typecheck  # next typegen && tsc --noEmit
npm run test:tdd   # Vitest (uma passada)
npm run build      # build de produção
```

Os mesmos quatro comandos rodam no job `Frontend` de
`.github/workflows/ci.yml`.

Os testes de componente simulam o cliente HTTP — eles provam o comportamento da
interface, não a integração com o backend real. Para conferir a jornada de
ponta a ponta, suba a API e o worker como descrito acima.

## Mapa de componentes

`INTERFACE.md`, na raiz, registra cada componente criado ou reaproveitado, sua
origem (primitive shadcn/ui ou composição própria) e as telas que o consomem.
Consulte-o antes de criar uma peça nova.
