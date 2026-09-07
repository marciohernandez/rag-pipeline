---
name: specsfy-specialist-tailwind-css
description: Implementar e revisar Tailwind CSS com tokens, variantes, responsividade, dark mode, container queries e CSS sustentável. Use quando houver tailwindcss ou utilitários Tailwind em templates; confirme a versão porque configuração e diretivas diferem entre gerações.
---

# Tailwind CSS

## Fluxo

1. Confirmar versão, integração, fonte de tokens e componentes existentes.
2. Traduzir layout e estados em constraints responsivas.
3. Reutilizar tokens semânticos antes de valores arbitrários.
4. Implementar mobile-first, estados interativos e preferências do usuário.
5. Extrair componente quando houver unidade semântica, não só repetição visual.
6. Revisar conflitos, classes dinâmicas e CSS gerado.
7. Validar navegadores, temas, zoom e tamanhos extremos.

## Padrões

- Manter cor, spacing, radius e tipografia em tokens com nomes de intenção.
- Usar variantes para estado; não esconder comportamento em concatenação opaca.
- Evitar `@apply` como substituto geral de componentes.
- Garantir que classes construídas dinamicamente sejam detectáveis pelo build.
- Tratar dark mode, reduced motion, contrast e forced colors conscientemente.
- Preferir layout fluido e container queries quando o componente depende do contêiner.
- Não multiplicar valores arbitrários sem justificar novo token.

## Validação

- Build de produção e inspeção de estilos ausentes.
- Viewports, containers, zoom 200/400%, tema e conteúdo longo.
- Hover, focus-visible, disabled, loading, error e selected.
- Contraste e preferência por movimento reduzido.

Leia [references/standards.md](references/standards.md) para tokens,
responsividade, variantes, acessibilidade e migração.
