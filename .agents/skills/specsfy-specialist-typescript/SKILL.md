---
name: specsfy-specialist-typescript
description: Modelar e revisar TypeScript seguro com strictness, narrowing, generics, modules, declarations, validação runtime e APIs públicas. Use para tsconfig, tipos, erros de compilação, bibliotecas ou contratos TS/JS; não confunda tipos estáticos com validação de dados externos.
---

# TypeScript

## Fluxo

1. Ler `tsconfig`, package type, bundler, runtime e versões.
2. Identificar fronteiras não confiáveis e tipos públicos.
3. Modelar estados válidos com unions, narrowing e invariantes.
4. Inferir internamente e anotar APIs onde o contrato precisa ser estável.
5. Eliminar `any`, assertions e `!` injustificados na área alterada.
6. Validar dados externos em runtime antes de tipá-los.
7. Rodar typecheck, testes, lint e build nos targets reais.

## Padrões

- Ativar opções strict compatíveis e corrigir erros sem casts cosméticos.
- Preferir unions discriminadas a combinações inválidas de booleanos.
- Usar `unknown` em fronteiras e narrowing explícito.
- Manter generics mínimos e vinculados a relações reais entre valores.
- Evitar enums quando objetos literais ou unions preservam interoperabilidade.
- Separar type-only imports e respeitar ESM/CJS do projeto.
- Testar tipos públicos quando regressões de inferência forem relevantes.

## Validação

- Typecheck sem emissão e build de todos os targets.
- Testes runtime das validações e serialização.
- API declarations quando biblioteca; compatibilidade de consumers.
- Busca focal por suppressions, casts duplos e tipos duplicados.

Leia [references/standards.md](references/standards.md) para modelagem,
configuração, módulos, bibliotecas e validação runtime.
