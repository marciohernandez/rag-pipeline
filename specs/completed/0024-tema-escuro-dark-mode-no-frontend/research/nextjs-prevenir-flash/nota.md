# Nota de proveniência: prevenir o flash antes da hidratação (Next.js)

## Origem

- Documento local: `frontend/node_modules/next/dist/docs/01-app/02-guides/preventing-flash-before-hydration.md`, distribuído com o pacote `next` na versão 16.3.4 (licença MIT).
- Consultado em 2026-10-05. Instrução local que motivou a leitura: `frontend/AGENTS.md` pede ler o guia relevante em `node_modules/next/dist/docs/` antes de escrever código.
- O conteúdo do guia não foi copiado; esta nota registra só as conclusões próprias.

## Técnica

Para aplicar uma preferência que só o navegador conhece (tema salvo em `localStorage`), o guia recomenda um script em linha no `<head>` do layout raiz. Ele roda de forma síncrona durante a leitura do HTML e altera o elemento `<html>` antes da primeira pintura. O elemento alterado precisa de `suppressHydrationWarning`, e a leitura do armazenamento fica dentro de `try/catch`, porque o armazenamento pode estar indisponível.

## Impacto na SPEC-0024

- O mecanismo de tema usa script em linha no `<head>` do layout raiz e `suppressHydrationWarning` no `<html>`, sem biblioteca de tema.
- O script em linha é compatível com a CSP atual de `frontend/next.config.ts` (`script-src 'self' 'unsafe-inline'`).
- A tela de erro global (`frontend/src/app/global-error.tsx`) tem o próprio `<html>` e precisa do mesmo script.
- O guia mostra o atributo `data-theme`; esta spec usa a classe `dark` no `<html>`, porque o `globals.css` já define `@custom-variant dark (&:is(.dark *))` e o bloco `.dark`.
