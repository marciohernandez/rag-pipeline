# Padrões e referências TypeScript

## Modelagem

- Estado finito: union discriminada.
- Mapa de chaves: `Record` ou mapped type quando conjunto é fechado.
- Dados externos: schema runtime que produz tipo validado.
- Extensão pública: interface quando merge é desejado; type alias nos demais casos.
- Invariância importante: constructor/factory que impede estados inválidos.

## Fontes oficiais

- Handbook: https://www.typescriptlang.org/docs/handbook/intro.html
- Narrowing: https://www.typescriptlang.org/docs/handbook/2/narrowing.html
- Generics: https://www.typescriptlang.org/docs/handbook/2/generics.html
- Modules: https://www.typescriptlang.org/docs/handbook/modules.html
- TSConfig: https://www.typescriptlang.org/tsconfig/
- Declaration files: https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html
- Semantic Versioning: https://semver.org/
