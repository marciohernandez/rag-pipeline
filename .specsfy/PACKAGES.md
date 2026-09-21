# Pacotes e bibliotecas

> O frontend autocontido em `frontend/` usa npm; o inventário gerado abaixo
> reúne suas dependências diretas e transitivas a partir de `package.json` e
> do lockfile. As dependências Python continuam declaradas em `pyproject.toml`
> e resolvidas em `uv.lock`.
>
> O inventário Python direto fica em [`docs/packages.md`](../docs/packages.md).

<!-- specsfy:documentator:start -->
# Pacotes e bibliotecas

| Gerenciador | Escopo | Pacote | Versão | Finalidade | Fonte |
| --- | --- | --- | --- | --- | --- |
| npm | produção | @base-ui/react | ^1.8.0 | Base UI is a library of headless ('unstyled') React components and low-level hooks. You gain complete control over your app's CSS and accessibility features. | https://github.com/mui/base-ui |
| npm | produção | class-variance-authority | ^0.7.1 | Class Variance Authority 🧬 | https://github.com/joe-bell/cva |
| npm | produção | cn | ^0.2.5 | Fast, small, compiled class-name merging for Tailwind CSS. Drop-in replacement for clsx + tailwind-merge. | https://github.com/shadcn-ui/cn |
| npm | produção | lucide-react | ^1.41.0 | A Lucide icon library package for React applications. | https://github.com/lucide-icons/lucide |
| npm | produção | next | 16.3.4 | The React Framework | vercel/next.js |
| npm | produção | react | 19.2.8 | React is a JavaScript library for building user interfaces. | https://github.com/react/react |
| npm | produção | react-dom | 19.2.8 | React package for working with the DOM. | https://github.com/react/react |
| npm | produção | shadcn | ^4.21.0 | Add components to your apps. | https://github.com/shadcn-ui/ui |
| npm | produção | tw-animate-css | ^1.4.0 | TailwindCSS v4.0 compatible replacement for `tailwindcss-animate`. | Wombosvideo/tw-animate-css |
| npm | desenvolvimento | @tailwindcss/postcss | ^4 | PostCSS plugin for Tailwind CSS, a utility-first CSS framework for rapidly building custom user interfaces | https://github.com/tailwindlabs/tailwindcss |
| npm | desenvolvimento | @testing-library/dom | ^10.4.1 | Simple and complete DOM testing utilities that encourage good testing practices. | https://github.com/testing-library/dom-testing-library |
| npm | desenvolvimento | @testing-library/jest-dom | ^7.0.1 | Custom jest matchers to test the state of the DOM | https://github.com/testing-library/jest-dom |
| npm | desenvolvimento | @testing-library/react | ^16.3.3 | Simple and complete React DOM testing utilities that encourage good testing practices. | https://github.com/testing-library/react-testing-library |
| npm | desenvolvimento | @testing-library/user-event | ^14.6.7 | Fire events the same way the user does | https://github.com/testing-library/user-event |
| npm | desenvolvimento | @types/node | ^24.13.3 | TypeScript definitions for node | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | desenvolvimento | @types/react | ^19 | TypeScript definitions for react | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | desenvolvimento | @types/react-dom | ^19 | TypeScript definitions for react-dom | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | desenvolvimento | @vitejs/plugin-react | ^6.1.1 | The default Vite plugin for React projects | https://github.com/vitejs/vite-plugin-react |
| npm | desenvolvimento | eslint | ^9 | An AST-based pattern checker for JavaScript. | eslint/eslint |
| npm | desenvolvimento | eslint-config-next | 16.3.4 | ESLint configuration used by Next.js. | vercel/next.js |
| npm | desenvolvimento | jsdom | ^30.0.1 | A JavaScript implementation of many web standards | https://github.com/jsdom/jsdom |
| npm | desenvolvimento | tailwindcss | ^4 | A utility-first CSS framework for rapidly building custom user interfaces. | https://github.com/tailwindlabs/tailwindcss |
| npm | desenvolvimento | typescript | ^5 | TypeScript is a language for application scale JavaScript development | https://github.com/microsoft/TypeScript |
| npm | desenvolvimento | vite-tsconfig-paths | ^6.1.1 | Vite resolver for TypeScript compilerOptions.paths | aleclarson/vite-tsconfig-paths |
| npm | desenvolvimento | vitest | ^5.0.0 | Next generation testing framework powered by Vite | https://github.com/vitest-dev/vitest |
| npm | transitiva | @adobe/css-tools | 4.5.0 | A modern CSS parser and stringifier with TypeScript support | https://github.com/adobe/css-tools |
| npm | transitiva | @alloc/quick-lru | 5.3.0 | Simple “Least Recently Used” (LRU) cache | https://github.com/aleclarson/quick-lru |
| npm | transitiva | @asamuzakjp/css-color | 6.0.7 | CSS color - Resolve and convert CSS colors. | https://github.com/asamuzaK/cssColor |
| npm | transitiva | lru-cache | 11.5.2 | A cache object that deletes the least-recently-used items. | git://github.com/isaacs/node-lru-cache |
| npm | transitiva | @asamuzakjp/dom-selector | 8.3.2 | A CSS selector engine. | https://github.com/asamuzaK/domSelector |
| npm | transitiva | @babel/code-frame | 7.29.7 | Generate errors that contain a code frame that point to source locations. | https://github.com/babel/babel |
| npm | transitiva | @babel/compat-data | 7.29.7 | The compat-data to determine required Babel plugins | https://github.com/babel/babel |
| npm | transitiva | @babel/core | 7.29.7 | Babel compiler core. | https://github.com/babel/babel |
| npm | transitiva | @babel/generator | 7.29.8 | Turns an AST into code. | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-annotate-as-pure | 7.29.7 | Helper function to annotate paths and nodes with #__PURE__ comment | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-compilation-targets | 7.29.7 | Helper functions on Babel compilation targets | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-create-class-features-plugin | 7.29.7 | Compile class public and private fields, private methods and decorators to ES6 | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-globals | 7.29.7 | A collection of JavaScript globals for Babel internal usage | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-member-expression-to-functions | 7.29.7 | Helper function to replace certain member expressions with function calls | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-module-imports | 7.29.7 | Babel helper functions for inserting module loads | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-module-transforms | 7.29.7 | Babel helper functions for implementing ES6 module transformations | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-optimise-call-expression | 7.29.7 | Helper function to optimise call expression | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-plugin-utils | 7.29.7 | General utilities for plugins to use | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-replace-supers | 7.29.7 | Helper function to replace supers | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-skip-transparent-expression-wrappers | 7.29.7 | Helper which skips types and parentheses | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-string-parser | 7.29.7 | A utility package to parse strings | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-validator-identifier | 7.29.7 | Validate identifier/keywords name | https://github.com/babel/babel |
| npm | transitiva | @babel/helper-validator-option | 7.29.7 | Validate plugin/preset options | https://github.com/babel/babel |
| npm | transitiva | @babel/helpers | 7.29.7 | Collection of helper functions used by Babel transforms. | https://github.com/babel/babel |
| npm | transitiva | @babel/parser | 7.29.8 | A JavaScript parser | https://github.com/babel/babel |
| npm | transitiva | @babel/plugin-syntax-jsx | 7.29.7 | Allow parsing of jsx | https://github.com/babel/babel |
| npm | transitiva | @babel/plugin-syntax-typescript | 7.29.7 | Allow parsing of TypeScript syntax | https://github.com/babel/babel |
| npm | transitiva | @babel/plugin-transform-modules-commonjs | 7.29.7 | This plugin transforms ES2015 modules to CommonJS | https://github.com/babel/babel |
| npm | transitiva | @babel/plugin-transform-typescript | 7.29.7 | Transform TypeScript into ES.next | https://github.com/babel/babel |
| npm | transitiva | @babel/preset-typescript | 7.29.7 | Babel preset for TypeScript. | https://github.com/babel/babel |
| npm | transitiva | @babel/runtime | 7.29.7 | babel's modular runtime helpers | https://github.com/babel/babel |
| npm | transitiva | @babel/template | 7.29.7 | Generate an AST from a string template. | https://github.com/babel/babel |
| npm | transitiva | @babel/traverse | 7.29.8 | The Babel Traverse module maintains the overall tree state, and is responsible for replacing, removing, and adding nodes | https://github.com/babel/babel |
| npm | transitiva | @babel/types | 7.29.8 | Babel Types is a Lodash-esque utility library for AST nodes | https://github.com/babel/babel |
| npm | transitiva | @base-ui/react | 1.8.0 | Base UI is a library of headless ('unstyled') React components and low-level hooks. You gain complete control over your app's CSS and accessibility features. | https://github.com/mui/base-ui |
| npm | transitiva | @base-ui/utils | 0.4.0 | A collection of React utility functions for Base UI. | https://github.com/mui/base-ui |
| npm | transitiva | @bramus/specificity | 2.4.2 | Calculate specificity of a CSS Selector | https://github.com/bramus/specificity |
| npm | transitiva | @csstools/color-helpers | 6.1.1 | Color helpers to ease transformation between formats, gamut, etc | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @csstools/css-calc | 3.3.0 | Solve CSS math expressions | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @csstools/css-color-parser | 4.2.2 | Parse CSS color values | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @csstools/css-parser-algorithms | 4.0.0 | Algorithms to help you parse CSS from an array of tokens. | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @csstools/css-syntax-patches-for-csstree | 1.1.12 | CSS syntax patches for CSS tree | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @csstools/css-tokenizer | 4.0.0 | Tokenize CSS | https://github.com/csstools/postcss-plugins |
| npm | transitiva | @dotenvx/dotenvx | 1.75.1 | a secure dotenv–from the creator of `dotenv` | https://github.com/dotenvx/dotenvx |
| npm | transitiva | commander | 11.1.0 | the complete solution for node.js command-line programs | https://github.com/tj/commander.js |
| npm | transitiva | define-lazy-prop | 2.0.0 | Define a lazily evaluated property on an object | sindresorhus/define-lazy-prop |
| npm | transitiva | execa | 5.1.1 | Process execution for humans | sindresorhus/execa |
| npm | transitiva | fdir | 6.5.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | get-stream | 6.0.1 | Get a stream as a string, Buffer, ArrayBuffer or array | sindresorhus/get-stream |
| npm | transitiva | human-signals | 2.1.0 | Human-friendly process signals | https://github.com/ehmicky/human-signals |
| npm | transitiva | is-docker | 2.2.1 | Check if the process is running inside a Docker container | sindresorhus/is-docker |
| npm | transitiva | is-stream | 2.0.1 | Check if something is a Node.js stream | sindresorhus/is-stream |
| npm | transitiva | is-wsl | 2.2.0 | Check if the process is running inside Windows Subsystem for Linux (Bash on Windows) | sindresorhus/is-wsl |
| npm | transitiva | isexe | 3.1.5 | Minimal module to check if a file is executable. | https://github.com/isaacs/isexe |
| npm | transitiva | npm-run-path | 4.0.1 | Get your PATH prepended with locally installed binaries | sindresorhus/npm-run-path |
| npm | transitiva | open | 8.4.2 | Open stuff like URLs, files, executables. Cross-platform. | sindresorhus/open |
| npm | transitiva | picomatch | 4.0.7 | Blazing fast and accurate glob matcher written in JavaScript, with no dependencies and full support for standard and extended Bash glob features, including braces, extglobs, POSIX brackets, and regular expressions. | micromatch/picomatch |
| npm | transitiva | signal-exit | 3.0.7 | when you want to fire an event no matter how a process exits. | https://github.com/tapjs/signal-exit |
| npm | transitiva | strip-final-newline | 2.0.0 | Strip the final newline character from a string or Uint8Array | sindresorhus/strip-final-newline |
| npm | transitiva | undici | 7.29.1 | An HTTP/1.1 client, written from scratch for Node.js | https://github.com/nodejs/undici |
| npm | transitiva | which | 4.0.0 | Like which(1) unix command. Find the first instance of an executable in the PATH. | git://github.com/isaacs/node-which |
| npm | transitiva | @dotenvx/primitives | 0.8.0 | a secure dotenv–from the creator of `dotenv` | https://github.com/dotenvx/dotenvx |
| npm | transitiva | @emnapi/core | 1.10.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @emnapi/runtime | 1.11.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @emnapi/wasi-threads | 1.2.1 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @eslint-community/eslint-utils | 4.10.1 | Utilities for ESLint plugins. | https://github.com/eslint-community/eslint-utils |
| npm | transitiva | eslint-visitor-keys | 3.4.3 | Constants and utilities about visitor keys to traverse AST. | https://github.com/eslint/js |
| npm | transitiva | @eslint-community/regexpp | 4.12.2 | Regular expression parser for ECMAScript. | https://github.com/eslint-community/regexpp |
| npm | transitiva | @eslint/config-array | 0.21.2 | General purpose glob-based configuration matching. | https://github.com/eslint/rewrite |
| npm | transitiva | @eslint/config-helpers | 0.4.2 | Helper utilities for creating ESLint configuration | https://github.com/eslint/rewrite |
| npm | transitiva | @eslint/core | 0.17.0 | Runtime-agnostic core of ESLint | https://github.com/eslint/rewrite |
| npm | transitiva | @eslint/eslintrc | 3.3.7 | The legacy ESLintRC config file format for ESLint | eslint/eslintrc |
| npm | transitiva | @eslint/js | 9.39.5 | ESLint JavaScript language implementation | https://github.com/eslint/eslint |
| npm | transitiva | @eslint/object-schema | 2.1.7 | An object schema merger/validator | https://github.com/eslint/rewrite |
| npm | transitiva | @eslint/plugin-kit | 0.4.1 | Utilities for building ESLint plugins. | https://github.com/eslint/rewrite |
| npm | transitiva | @exodus/bytes | 1.15.1 | Various operations on Uint8Array data | https://github.com/ExodusOSS/bytes |
| npm | transitiva | @floating-ui/core | 1.8.0 | Positioning library for floating elements: tooltips, popovers, dropdowns, and more | https://github.com/floating-ui/floating-ui |
| npm | transitiva | @floating-ui/dom | 1.8.0 | Floating UI for the web | https://github.com/floating-ui/floating-ui |
| npm | transitiva | @floating-ui/react-dom | 2.1.9 | Floating UI for React DOM | https://github.com/floating-ui/floating-ui |
| npm | transitiva | @floating-ui/utils | 0.2.12 | Utilities for Floating UI | https://github.com/floating-ui/floating-ui |
| npm | transitiva | @hono/node-server | 2.1.1 | Node.js Adapter for Hono | https://github.com/honojs/node-server |
| npm | transitiva | @humanfs/core | 0.19.2 | The core of the humanfs library. | https://github.com/humanwhocodes/humanfs |
| npm | transitiva | @humanfs/node | 0.16.8 | The Node.js bindings of the humanfs library. | https://github.com/humanwhocodes/humanfs |
| npm | transitiva | @humanfs/types | 0.15.0 | The TypeScript types for the hfs project. | https://github.com/humanwhocodes/humanfs |
| npm | transitiva | @humanwhocodes/module-importer | 1.0.1 | Universal module importer for Node.js | https://github.com/humanwhocodes/module-importer |
| npm | transitiva | @humanwhocodes/retry | 0.4.3 | A utility to retry failed async methods. | https://github.com/humanwhocodes/retry |
| npm | transitiva | @img/colour | 1.1.0 | The ESM-only 'color' package made compatible for use with CommonJS runtimes | https://github.com/lovell/colour |
| npm | transitiva | @img/sharp-darwin-arm64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-darwin-x64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-freebsd-wasm32 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-darwin-arm64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-darwin-x64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-arm | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-arm64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-ppc64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-riscv64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-s390x | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linux-x64 | 1.3.3 | Prebuilt libvips and dependencies for use with sharp on Linux (glibc) x64 | https://github.com/lovell/sharp-libvips |
| npm | transitiva | @img/sharp-libvips-linuxmusl-arm64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-libvips-linuxmusl-x64 | 1.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-arm | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-arm64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-ppc64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-riscv64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-s390x | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linux-x64 | 0.35.4 | Prebuilt sharp for use with Linux (glibc) x64 | https://github.com/lovell/sharp |
| npm | transitiva | @img/sharp-linuxmusl-arm64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-linuxmusl-x64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-wasm32 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-webcontainers-wasm32 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-win32-arm64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-win32-ia32 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @img/sharp-win32-x64 | 0.35.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @jridgewell/gen-mapping | 0.3.13 | Generate source maps | https://github.com/jridgewell/sourcemaps |
| npm | transitiva | @jridgewell/remapping | 2.3.5 | Remap sequential sourcemaps through transformations to point at the original source code | https://github.com/jridgewell/sourcemaps |
| npm | transitiva | @jridgewell/resolve-uri | 3.1.2 | Resolve a URI relative to an optional base URI | https://github.com/jridgewell/resolve-uri |
| npm | transitiva | @jridgewell/sourcemap-codec | 1.6.0 | Encode/decode sourcemap mappings | https://github.com/jridgewell/sourcemaps |
| npm | transitiva | @jridgewell/trace-mapping | 0.3.31 | Trace the original position through a source map | https://github.com/jridgewell/sourcemaps |
| npm | transitiva | @modelcontextprotocol/sdk | 1.30.0 | Model Context Protocol implementation for TypeScript | https://github.com/modelcontextprotocol/typescript-sdk |
| npm | transitiva | ajv | 8.20.0 | Another JSON Schema Validator | https://github.com/ajv-validator/ajv |
| npm | transitiva | json-schema-traverse | 1.0.0 | Traverse JSON Schema passing each schema object to callback | https://github.com/epoberezkin/json-schema-traverse |
| npm | transitiva | @napi-rs/wasm-runtime | 1.2.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/env | 16.3.4 | Next.js dotenv file loading | https://github.com/vercel/next.js |
| npm | transitiva | @next/eslint-plugin-next | 16.3.4 | ESLint plugin for Next.js. | vercel/next.js |
| npm | transitiva | @eslint-community/eslint-utils | 4.9.1 | Utilities for ESLint plugins. | https://github.com/eslint-community/eslint-utils |
| npm | transitiva | @next/swc-darwin-arm64 | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-darwin-x64 | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-linux-arm64-gnu | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-linux-arm64-musl | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-linux-x64-gnu | 16.3.4 | Finalidade não descrita nos metadados locais. | https://github.com/vercel/next.js |
| npm | transitiva | @next/swc-linux-x64-musl | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-win32-arm64-msvc | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @next/swc-win32-x64-msvc | 16.3.4 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @nodelib/fs.scandir | 2.1.5 | List files and directories inside the specified directory | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.scandir |
| npm | transitiva | @nodelib/fs.stat | 2.0.5 | Get the status of a file with some features | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.stat |
| npm | transitiva | @nodelib/fs.walk | 1.2.8 | A library for efficiently walking a directory recursively | https://github.com/nodelib/nodelib/tree/master/packages/fs/fs.walk |
| npm | transitiva | @nolyfill/is-core-module | 1.0.39 | Finalidade não descrita nos metadados locais. | https://github.com/SukkaW/nolyfill |
| npm | transitiva | @oxc-project/types | 0.148.0 | Types for Oxc AST nodes | https://github.com/oxc-project/oxc |
| npm | transitiva | @rolldown/binding-android-arm-eabi | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-android-arm64 | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-darwin-arm64 | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-darwin-x64 | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-freebsd-x64 | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-arm-gnueabihf | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-arm64-gnu | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-arm64-musl | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-ppc64-gnu | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-s390x-gnu | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-linux-x64-gnu | 1.2.7 | Fast JavaScript/TypeScript bundler in Rust with Rollup-compatible API. | https://github.com/rolldown/rolldown |
| npm | transitiva | @rolldown/binding-linux-x64-musl | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-openharmony-arm64 | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-win32-arm64-msvc | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/binding-win32-x64-msvc | 1.2.7 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @rolldown/pluginutils | 1.0.1 | Plugin utilities for Rolldown | https://github.com/rolldown/plugins |
| npm | transitiva | @rtsao/scc | 1.1.0 | Finalidade não descrita nos metadados locais. | rtsao/scc |
| npm | transitiva | @sec-ant/readable-stream | 0.4.1 | A tiny, zero-dependency yet spec-compliant asynchronous iterator polyfill/ponyfill for ReadableStreams. | https://github.com/Sec-ant/readable-stream |
| npm | transitiva | @sindresorhus/merge-streams | 4.0.0 | Merge multiple streams into a unified stream | sindresorhus/merge-streams |
| npm | transitiva | @swc/helpers | 0.5.23 | External helpers for the swc project. | https://github.com/swc-project/swc |
| npm | transitiva | @tailwindcss/node | 4.3.3 | A utility-first CSS framework for rapidly building custom user interfaces. | https://github.com/tailwindlabs/tailwindcss |
| npm | transitiva | @tailwindcss/oxide | 4.3.3 | Finalidade não descrita nos metadados locais. | https://github.com/tailwindlabs/tailwindcss |
| npm | transitiva | @tailwindcss/oxide-android-arm64 | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-darwin-arm64 | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-darwin-x64 | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-freebsd-x64 | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-linux-arm-gnueabihf | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-linux-arm64-gnu | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-linux-arm64-musl | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-linux-x64-gnu | 4.3.3 | Finalidade não descrita nos metadados locais. | https://github.com/tailwindlabs/tailwindcss |
| npm | transitiva | @tailwindcss/oxide-linux-x64-musl | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-wasm32-wasi | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-win32-arm64-msvc | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/oxide-win32-x64-msvc | 4.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @tailwindcss/postcss | 4.3.3 | PostCSS plugin for Tailwind CSS, a utility-first CSS framework for rapidly building custom user interfaces | https://github.com/tailwindlabs/tailwindcss |
| npm | transitiva | @testing-library/dom | 10.4.1 | Simple and complete DOM testing utilities that encourage good testing practices. | https://github.com/testing-library/dom-testing-library |
| npm | transitiva | aria-query | 5.3.0 | Programmatic access to the ARIA specification | https://github.com/A11yance/aria-query |
| npm | transitiva | @testing-library/jest-dom | 7.0.1 | Custom jest matchers to test the state of the DOM | https://github.com/testing-library/jest-dom |
| npm | transitiva | dom-accessibility-api | 0.6.3 | Implements https://w3c.github.io/accname/ | https://github.com/eps1lon/dom-accessibility-api |
| npm | transitiva | @testing-library/react | 16.3.3 | Simple and complete React DOM testing utilities that encourage good testing practices. | https://github.com/testing-library/react-testing-library |
| npm | transitiva | @testing-library/user-event | 14.6.7 | Fire events the same way the user does | https://github.com/testing-library/user-event |
| npm | transitiva | @ts-morph/common | 0.27.0 | Common functionality for ts-morph packages. | https://github.com/dsherret/ts-morph |
| npm | transitiva | balanced-match | 4.0.4 | Match balanced character pairs, like "{" and "}" | git://github.com/juliangruber/balanced-match |
| npm | transitiva | brace-expansion | 5.0.9 | Brace expansion as known from sh/bash | git://github.com/juliangruber/brace-expansion |
| npm | transitiva | fast-glob | 3.3.3 | It's a very fast and efficient glob library for Node.js | mrmlnc/fast-glob |
| npm | transitiva | glob-parent | 5.1.2 | Extract the non-magic parent path from a glob string. | gulpjs/glob-parent |
| npm | transitiva | minimatch | 10.2.6 | a glob matcher in javascript | git://github.com/isaacs/minimatch |
| npm | transitiva | @tybys/wasm-util | 0.10.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @types/aria-query | 5.0.4 | TypeScript definitions for aria-query | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/chai | 5.2.3 | TypeScript definitions for chai | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/deep-eql | 4.0.2 | TypeScript definitions for deep-eql | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/estree | 1.0.9 | TypeScript definitions for estree | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/json-schema | 7.0.15 | TypeScript definitions for json-schema | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/json5 | 0.0.29 | TypeScript definitions for JSON5 | https://www.github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/node | 24.13.3 | TypeScript definitions for node | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/react | 19.2.18 | TypeScript definitions for react | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/react-dom | 19.2.7 | TypeScript definitions for react-dom | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @types/validate-npm-package-name | 4.0.2 | TypeScript definitions for validate-npm-package-name | https://github.com/DefinitelyTyped/DefinitelyTyped |
| npm | transitiva | @typescript-eslint/eslint-plugin | 8.69.0 | TypeScript plugin for ESLint | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | ignore | 7.0.8 | Ignore is a manager and filter for .gitignore rules, the one used by eslint, gitbook and many others. | git@github.com:kaelzhang/node-ignore |
| npm | transitiva | @typescript-eslint/parser | 8.69.0 | An ESLint custom parser which leverages TypeScript ESTree | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/project-service | 8.69.0 | Standalone TypeScript project service wrapper for linting. | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/scope-manager | 8.69.0 | TypeScript scope analyser for ESLint | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/tsconfig-utils | 8.69.0 | Utilities for collecting TSConfigs for linting scenarios. | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/type-utils | 8.69.0 | Type utilities for working with TypeScript + ESLint together | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/types | 8.69.0 | Types for the TypeScript-ESTree AST spec | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/typescript-estree | 8.69.0 | A parser that converts TypeScript source code into an ESTree compatible form | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | semver | 7.8.5 | The semantic version parser used by npm. | https://github.com/npm/node-semver |
| npm | transitiva | @typescript-eslint/utils | 8.69.0 | Utilities for working with TypeScript + ESLint together | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | @typescript-eslint/visitor-keys | 8.69.0 | Visitor keys used to help traverse the TypeScript-ESTree AST | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | eslint-visitor-keys | 5.0.1 | Constants and utilities about visitor keys to traverse AST. | https://github.com/eslint/js |
| npm | transitiva | @unrs/resolver-binding-android-arm-eabi | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-android-arm64 | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-darwin-arm64 | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-darwin-x64 | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-freebsd-x64 | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-arm-gnueabihf | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-arm-musleabihf | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-arm64-gnu | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-arm64-musl | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-loong64-gnu | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-loong64-musl | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-ppc64-gnu | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-riscv64-gnu | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-riscv64-musl | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-s390x-gnu | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-linux-x64-gnu | 1.12.2 | UnRS Resolver Node API | https://github.com/unrs/unrs-resolver |
| npm | transitiva | @unrs/resolver-binding-linux-x64-musl | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-openharmony-arm64 | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-wasm32-wasi | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @emnapi/runtime | 1.10.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-win32-arm64-msvc | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-win32-ia32-msvc | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @unrs/resolver-binding-win32-x64-msvc | 1.12.2 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | @vitejs/plugin-react | 6.1.1 | The default Vite plugin for React projects | https://github.com/vitejs/vite-plugin-react |
| npm | transitiva | @vitest/mocker | 5.0.0 | Vitest module mocker implementation | https://github.com/vitest-dev/vitest |
| npm | transitiva | magic-string | 1.2.3 | Modify strings, generate sourcemaps | https://github.com/Rich-Harris/magic-string |
| npm | transitiva | @vitest/spy | 5.0.0 | Lightweight Jest compatible spy implementation | https://github.com/vitest-dev/vitest |
| npm | transitiva | accepts | 2.0.0 | Higher-level content negotiation | jshttp/accepts |
| npm | transitiva | acorn | 8.18.0 | ECMAScript parser | https://github.com/acornjs/acorn |
| npm | transitiva | acorn-jsx | 5.3.2 | Modern, fast React.js JSX parser | https://github.com/acornjs/acorn-jsx |
| npm | transitiva | ajv | 6.15.0 | Another JSON Schema Validator | https://github.com/ajv-validator/ajv |
| npm | transitiva | ajv-formats | 3.0.1 | Format validation for Ajv v7+ | https://github.com/ajv-validator/ajv-formats |
| npm | transitiva | ansi-colors | 4.1.3 | Easily add ANSI colors to your text and symbols in the terminal. A faster drop-in replacement for chalk, kleur and turbocolor (without the dependencies and rendering bugs). | doowb/ansi-colors |
| npm | transitiva | ansi-regex | 5.0.1 | Regular expression for matching ANSI escape codes | chalk/ansi-regex |
| npm | transitiva | ansi-styles | 4.3.0 | ANSI escape codes for styling strings in the terminal | chalk/ansi-styles |
| npm | transitiva | argparse | 2.0.1 | CLI arguments parser. Native port of python's argparse. | nodeca/argparse |
| npm | transitiva | aria-query | 5.3.2 | Programmatic access to the ARIA specification | https://github.com/A11yance/aria-query |
| npm | transitiva | array-buffer-byte-length | 1.0.2 | Get the byte length of an ArrayBuffer, even in engines without a `.byteLength` method. | https://github.com/inspect-js/array-buffer-byte-length |
| npm | transitiva | array-includes | 3.1.9 | An ES7/ES2016 spec-compliant `Array.prototype.includes` shim/polyfill/replacement that works as far down as ES3. | git://github.com/es-shims/array-includes |
| npm | transitiva | array.prototype.findlast | 1.2.5 | An ESnext spec-compliant `Array.prototype.findLast` shim/polyfill/replacement that works as far down as ES3. | https://github.com/es-shims/Array.prototype.findLast |
| npm | transitiva | array.prototype.findlastindex | 1.2.6 | An ESnext spec-compliant `Array.prototype.findLastIndex` shim/polyfill/replacement that works as far down as ES3. | https://github.com/es-shims/Array.prototype.findLastIndex |
| npm | transitiva | array.prototype.flat | 1.3.3 | An ES2019 spec-compliant `Array.prototype.flat` shim/polyfill/replacement that works as far down as ES3. | git://github.com/es-shims/Array.prototype.flat |
| npm | transitiva | array.prototype.flatmap | 1.3.3 | An ES2019 spec-compliant `Array.prototype.flatMap` shim/polyfill/replacement that works as far down as ES3. | git://github.com/es-shims/Array.prototype.flatMap |
| npm | transitiva | array.prototype.tosorted | 1.1.4 | An ESnext spec-compliant `Array.prototype.toSorted` shim/polyfill/replacement that works as far down as ES3. | https://github.com/es-shims/Array.prototype.toSorted |
| npm | transitiva | arraybuffer.prototype.slice | 1.0.4 | ES spec-compliant shim for ArrayBuffer.prototype.slice | https://github.com/es-shims/ArrayBuffer.prototype.slice |
| npm | transitiva | assertion-error | 2.0.1 | Error constructor for test and validation frameworks that implements standardized AssertionError specification. | git@github.com:chaijs/assertion-error |
| npm | transitiva | ast-types | 0.16.3 | Esprima-compatible implementation of the Mozilla JS Parser API | https://github.com/benjamn/ast-types |
| npm | transitiva | ast-types-flow | 0.0.8 | Flow types for the Javascript AST | https://github.com/kyldvs/ast-types-flow |
| npm | transitiva | async-function | 1.0.0 | A function that returns the normally hidden `AsyncFunction` constructor | https://github.com/ljharb/async-function |
| npm | transitiva | atomically | 1.7.0 | Read and write files atomically and reliably. | https://github.com/fabiospampinato/atomically |
| npm | transitiva | available-typed-arrays | 1.0.7 | Returns an array of Typed Array names that are available in the current environment | https://github.com/inspect-js/available-typed-arrays |
| npm | transitiva | axe-core | 4.13.0 | Accessibility engine for automated Web UI testing | https://github.com/dequelabs/axe-core |
| npm | transitiva | axobject-query | 4.1.0 | Programmatic access to information about the AXObject Model | https://github.com/A11yance/axobject-query |
| npm | transitiva | balanced-match | 1.0.2 | Match balanced character pairs, like "{" and "}" | git://github.com/juliangruber/balanced-match |
| npm | transitiva | baseline-browser-mapping | 2.11.21 | A library for obtaining browser versions with their maximum supported Baseline feature set and Widely Available status. | https://github.com/web-platform-dx/baseline-browser-mapping |
| npm | transitiva | bidi-js | 1.0.3 | A JavaScript implementation of the Unicode Bidirectional Algorithm | https://github.com/lojjic/bidi-js |
| npm | transitiva | body-parser | 2.3.0 | Node.js body parsing middleware | expressjs/body-parser |
| npm | transitiva | content-type | 2.1.0 | Create and parse HTTP Content-Type header | jshttp/content-type |
| npm | transitiva | brace-expansion | 1.1.18 | Brace expansion as known from sh/bash | git://github.com/juliangruber/brace-expansion |
| npm | transitiva | braces | 3.0.3 | Bash-like brace expansion, implemented in JavaScript. Safer than other brace expansion libs, with complete support for the Bash 4.3 braces specification, without sacrificing speed. | micromatch/braces |
| npm | transitiva | browserslist | 4.28.9 | Share target browsers between different front-end tools, like Autoprefixer, Stylelint and babel-env-preset | browserslist/browserslist |
| npm | transitiva | bundle-name | 4.1.0 | Get bundle name from a bundle identifier (macOS): `com.apple.Safari` → `Safari` | sindresorhus/bundle-name |
| npm | transitiva | bytes | 3.1.2 | Utility to parse a string bytes to bytes and vice-versa | visionmedia/bytes.js |
| npm | transitiva | call-bind | 1.0.9 | Robustly `.call.bind()` a function | https://github.com/ljharb/call-bind |
| npm | transitiva | call-bind-apply-helpers | 1.0.2 | Helper functions around Function call/apply/bind, for use in `call-bind` | https://github.com/ljharb/call-bind-apply-helpers |
| npm | transitiva | call-bound | 1.0.4 | Robust call-bound JavaScript intrinsics, using `call-bind` and `get-intrinsic`. | https://github.com/ljharb/call-bound |
| npm | transitiva | callsites | 3.1.0 | Get callsites from the V8 stack trace API | sindresorhus/callsites |
| npm | transitiva | caniuse-lite | 1.0.30001810 | A smaller version of caniuse-db, with only the essentials! | browserslist/caniuse-lite |
| npm | transitiva | chai | 6.2.2 | BDD/TDD assertion library for node.js and the browser. Test framework agnostic. | https://github.com/chaijs/chai |
| npm | transitiva | chalk | 4.1.2 | Terminal string styling done right | chalk/chalk |
| npm | transitiva | class-variance-authority | 0.7.1 | Class Variance Authority 🧬 | https://github.com/joe-bell/cva |
| npm | transitiva | cli-cursor | 5.0.0 | Toggle the CLI cursor | sindresorhus/cli-cursor |
| npm | transitiva | cli-spinners | 2.9.2 | Spinners for use in the terminal | sindresorhus/cli-spinners |
| npm | transitiva | client-only | 0.0.1 | This is a marker package to indicate that a module can only be used in Client Components. |  |
| npm | transitiva | clsx | 2.1.1 | A tiny (239B) utility for constructing className strings conditionally. | lukeed/clsx |
| npm | transitiva | cn | 0.2.5 | Fast, small, compiled class-name merging for Tailwind CSS. Drop-in replacement for clsx + tailwind-merge. | https://github.com/shadcn-ui/cn |
| npm | transitiva | code-block-writer | 13.0.3 | A simple code writer that assists with formatting and visualizing blocks of code. | https://github.com/dsherret/code-block-writer |
| npm | transitiva | color-convert | 2.0.1 | Plain color conversion functions | Qix-/color-convert |
| npm | transitiva | color-name | 1.1.4 | A list of color names and its values | git@github.com:colorjs/color-name |
| npm | transitiva | commander | 14.0.3 | the complete solution for node.js command-line programs | https://github.com/tj/commander.js |
| npm | transitiva | concat-map | 0.0.1 | concatenative mapdashery | git://github.com/substack/node-concat-map |
| npm | transitiva | conf | 10.2.0 | Simple config handling for your app or module | sindresorhus/conf |
| npm | transitiva | ajv-formats | 2.1.1 | Format validation for Ajv v7+ | https://github.com/ajv-validator/ajv-formats |
| npm | transitiva | json-schema-typed | 7.0.3 | JSON Schema TypeScript definitions with complete inline documentation. | https://github.com/RemyRylan/json-schema-typed |
| npm | transitiva | content-disposition | 1.1.0 | Create and parse Content-Disposition header | jshttp/content-disposition |
| npm | transitiva | content-type | 1.0.5 | Create and parse HTTP Content-Type header | jshttp/content-type |
| npm | transitiva | convert-source-map | 2.0.0 | Converts a source-map from/to  different formats and allows adding/changing properties. | git://github.com/thlorenz/convert-source-map |
| npm | transitiva | cookie | 0.7.2 | HTTP server cookie parsing and serialization | jshttp/cookie |
| npm | transitiva | cookie-signature | 1.2.2 | Sign and unsign cookies | https://github.com/visionmedia/node-cookie-signature |
| npm | transitiva | cors | 2.8.6 | Node.js CORS middleware | expressjs/cors |
| npm | transitiva | cosmiconfig | 9.0.2 | Find and load configuration from a package.json property, rc file, TypeScript module, and more! | https://github.com/cosmiconfig/cosmiconfig |
| npm | transitiva | cross-spawn | 7.0.6 | Cross platform child_process#spawn and child_process#spawnSync | git@github.com:moxystudio/node-cross-spawn |
| npm | transitiva | css-tree | 3.2.1 | A tool set for CSS: fast detailed parser (CSS → AST), walker (AST traversal), generator (AST → CSS) and lexer (validation and matching) based on specs and browser implementations | csstree/csstree |
| npm | transitiva | css.escape | 1.5.1 | A robust polyfill for the `CSS.escape` utility method as defined in CSSOM. | https://github.com/mathiasbynens/CSS.escape |
| npm | transitiva | cssesc | 3.0.0 | A JavaScript library for escaping CSS strings and identifiers while generating the shortest possible ASCII-only output. | https://github.com/mathiasbynens/cssesc |
| npm | transitiva | csstype | 3.2.3 | Strict TypeScript and Flow types for style based on MDN data | https://github.com/frenic/csstype |
| npm | transitiva | damerau-levenshtein | 1.0.8 | Damerau - Levenshtein distance by The Spanish Inquisition + relative distance | https://github.com/tad-lispy/node-damerau-levenshtein |
| npm | transitiva | data-urls | 7.0.0 | Parses data: URLs | https://github.com/jsdom/data-urls |
| npm | transitiva | whatwg-url | 16.0.1 | An implementation of the WHATWG URL Standard's URL API and parsing machinery | https://github.com/jsdom/whatwg-url |
| npm | transitiva | data-view-buffer | 1.0.2 | Get the ArrayBuffer out of a DataView, robustly. | https://github.com/inspect-js/data-view-buffer |
| npm | transitiva | data-view-byte-length | 1.0.2 | Get the byteLength out of a DataView, robustly. | https://github.com/inspect-js/data-view-byte-length |
| npm | transitiva | data-view-byte-offset | 1.0.1 | Get the byteOffset out of a DataView, robustly. | https://github.com/inspect-js/data-view-byte-offset |
| npm | transitiva | debounce-fn | 4.0.0 | Debounce a function | sindresorhus/debounce-fn |
| npm | transitiva | debug | 4.4.3 | Lightweight debugging utility for Node.js and the browser | git://github.com/debug-js/debug |
| npm | transitiva | decimal.js | 10.6.0 | An arbitrary-precision Decimal type for JavaScript. | https://github.com/MikeMcl/decimal.js |
| npm | transitiva | dedent | 1.7.2 | A string tag that strips indentation from multi-line strings. ⬅️ | https://github.com/dmnd/dedent |
| npm | transitiva | deep-is | 0.1.4 | node's assert.deepEqual algorithm except for NaN being equal to NaN | http://github.com/thlorenz/deep-is |
| npm | transitiva | deepmerge | 4.3.1 | A library for deep (recursive) merging of Javascript objects | git://github.com/TehShrike/deepmerge |
| npm | transitiva | default-browser | 5.5.1 | Get the default browser | sindresorhus/default-browser |
| npm | transitiva | default-browser-id | 5.0.1 | Get the bundle identifier of the default browser (macOS). Example: com.apple.Safari | sindresorhus/default-browser-id |
| npm | transitiva | define-data-property | 1.1.4 | Define a data property on an object. Will fall back to assignment in an engine without descriptors. | https://github.com/ljharb/define-data-property |
| npm | transitiva | define-lazy-prop | 3.0.0 | Define a lazily evaluated property on an object | sindresorhus/define-lazy-prop |
| npm | transitiva | define-properties | 1.2.1 | Define multiple non-enumerable properties at once. Uses `Object.defineProperty` when available; falls back to standard assignment in older engines. | git://github.com/ljharb/define-properties |
| npm | transitiva | depd | 2.0.0 | Deprecate all the things | dougwilson/nodejs-depd |
| npm | transitiva | dequal | 2.0.3 | A tiny (304B to 489B) utility for check for deep equality | lukeed/dequal |
| npm | transitiva | detect-libc | 2.1.2 | Node.js module to detect the C standard library (libc) implementation family and version | git://github.com/lovell/detect-libc |
| npm | transitiva | diff | 8.0.4 | A JavaScript text diff implementation. | https://github.com/kpdecker/jsdiff |
| npm | transitiva | doctrine | 2.1.0 | JSDoc parser | eslint/doctrine |
| npm | transitiva | dom-accessibility-api | 0.5.16 | Implements https://w3c.github.io/accname/ | https://github.com/eps1lon/dom-accessibility-api |
| npm | transitiva | dot-prop | 6.0.1 | Get, set, or delete a property from a nested object using a dot path | sindresorhus/dot-prop |
| npm | transitiva | dotenv | 17.4.2 | Loads environment variables from .env file | git://github.com/motdotla/dotenv |
| npm | transitiva | dunder-proto | 1.0.1 | If available, the `Object.prototype.__proto__` accessor and mutator, call-bound | https://github.com/es-shims/dunder-proto |
| npm | transitiva | ee-first | 1.1.1 | return the first event in a set of ee/event pairs | jonathanong/ee-first |
| npm | transitiva | electron-to-chromium | 1.5.422 | Provides a list of electron-to-chromium version mappings | https://github.com/Kilian/electron-to-chromium |
| npm | transitiva | emoji-regex | 9.2.2 | A regular expression to match all Emoji-only symbols as per the Unicode Standard. | https://github.com/mathiasbynens/emoji-regex |
| npm | transitiva | encodeurl | 2.0.0 | Encode a URL to a percent-encoded form, excluding already-encoded sequences | pillarjs/encodeurl |
| npm | transitiva | enhanced-resolve | 5.24.5 | Offers a async require.resolve function. It's highly configurable. | https://github.com/webpack/enhanced-resolve |
| npm | transitiva | enquirer | 2.4.1 | Stylish, intuitive and user-friendly prompt system. Fast and lightweight enough for small projects, powerful and extensible enough for the most advanced use cases. | enquirer/enquirer |
| npm | transitiva | entities | 8.0.0 | Encode & decode XML and HTML entities with ease & speed | https://github.com/fb55/entities |
| npm | transitiva | env-paths | 2.2.1 | Get paths for storing things like data, config, cache, etc | sindresorhus/env-paths |
| npm | transitiva | error-ex | 1.3.4 | Easy error subclassing and stack customization | qix-/node-error-ex |
| npm | transitiva | es-abstract | 1.24.2 | ECMAScript spec abstract operations. | git://github.com/ljharb/es-abstract |
| npm | transitiva | es-abstract-get | 1.0.0 | ECMAScript Abstract Operations for "getting properties" (Get, GetV, GetMethod) | https://github.com/ljharb/es-abstract-get |
| npm | transitiva | es-define-property | 1.0.1 | `Object.defineProperty`, but not IE 8's broken one. | https://github.com/ljharb/es-define-property |
| npm | transitiva | es-errors | 1.3.0 | A simple cache for a few of the JS Error constructors. | https://github.com/ljharb/es-errors |
| npm | transitiva | es-iterator-helpers | 1.4.0 | An ESnext spec-compliant iterator helpers shim/polyfill/replacement that works as far down as ES3. | https://github.com/es-shims/iterator-helpers |
| npm | transitiva | es-module-lexer | 2.3.2 | Lexes ES modules returning their import/export metadata | https://github.com/guybedford/es-module-lexer |
| npm | transitiva | es-object-atoms | 1.1.2 | ES Object-related atoms: Object, ToObject, RequireObjectCoercible | https://github.com/ljharb/es-object-atoms |
| npm | transitiva | es-set-tostringtag | 2.1.0 | A helper to optimistically set Symbol.toStringTag, when possible. | https://github.com/es-shims/es-set-tostringtag |
| npm | transitiva | es-shim-unscopables | 1.1.0 | Helper package to shim a method into `Array.prototype[Symbol.unscopables]` | https://github.com/ljharb/es-shim-unscopables |
| npm | transitiva | es-to-primitive | 1.3.4 | ECMAScript “ToPrimitive” algorithm. Provides ES5 and ES2015 versions. | git://github.com/ljharb/es-to-primitive |
| npm | transitiva | escalade | 3.2.0 | A tiny (183B to 210B) and fast utility to ascend parent directories | lukeed/escalade |
| npm | transitiva | escape-html | 1.0.3 | Escape string for use in HTML | component/escape-html |
| npm | transitiva | escape-string-regexp | 4.0.0 | Escape RegExp special characters | sindresorhus/escape-string-regexp |
| npm | transitiva | eslint | 9.39.5 | An AST-based pattern checker for JavaScript. | eslint/eslint |
| npm | transitiva | eslint-config-next | 16.3.4 | ESLint configuration used by Next.js. | vercel/next.js |
| npm | transitiva | globals | 16.4.0 | Global identifiers from different JavaScript environments | sindresorhus/globals |
| npm | transitiva | eslint-import-resolver-node | 0.3.10 | Node default behavior import resolution plugin for eslint-plugin-import. | https://github.com/import-js/eslint-plugin-import |
| npm | transitiva | debug | 3.2.7 | Lightweight debugging utility for Node.js and the browser | git://github.com/debug-js/debug |
| npm | transitiva | eslint-import-resolver-typescript | 3.10.1 | This plugin adds `TypeScript` support to `eslint-plugin-import` | https://github.com/import-js/eslint-import-resolver-typescript |
| npm | transitiva | eslint-module-utils | 2.14.0 | Core utilities to support eslint-plugin-import and other module-related plugins. | https://github.com/import-js/eslint-plugin-import |
| npm | transitiva | eslint-plugin-import | 2.32.0 | Import with sanity. | https://github.com/import-js/eslint-plugin-import |
| npm | transitiva | eslint-plugin-jsx-a11y | 6.10.2 | Static AST checker for accessibility rules on JSX elements. | https://github.com/jsx-eslint/eslint-plugin-jsx-a11y |
| npm | transitiva | eslint-plugin-react | 7.37.5 | React specific linting rules for ESLint | https://github.com/jsx-eslint/eslint-plugin-react |
| npm | transitiva | eslint-plugin-react-hooks | 7.1.1 | ESLint rules for React Hooks | https://github.com/facebook/react |
| npm | transitiva | eslint-scope | 8.4.0 | ECMAScript scope analyzer for ESLint | https://github.com/eslint/js |
| npm | transitiva | eslint-visitor-keys | 4.2.1 | Constants and utilities about visitor keys to traverse AST. | https://github.com/eslint/js |
| npm | transitiva | espree | 10.4.0 | An Esprima-compatible JavaScript parser built on Acorn | https://github.com/eslint/js |
| npm | transitiva | esprima | 4.0.1 | ECMAScript parsing infrastructure for multipurpose analysis | https://github.com/jquery/esprima |
| npm | transitiva | esquery | 1.7.0 | A query library for ECMAScript AST using a CSS selector like query language. | https://github.com/estools/esquery |
| npm | transitiva | esrecurse | 4.3.0 | ECMAScript AST recursive visitor | https://github.com/estools/esrecurse |
| npm | transitiva | estraverse | 5.3.0 | ECMAScript JS AST traversal functions | http://github.com/estools/estraverse |
| npm | transitiva | estree-walker | 3.0.3 | Traverse an ESTree-compliant AST | https://github.com/Rich-Harris/estree-walker |
| npm | transitiva | esutils | 2.0.3 | utility box for ECMAScript language tools | http://github.com/estools/esutils |
| npm | transitiva | etag | 1.8.1 | Create simple HTTP ETags | jshttp/etag |
| npm | transitiva | eventsource | 3.0.7 | WhatWG/W3C compliant EventSource client for Node.js and browsers | git://git@github.com/EventSource/eventsource |
| npm | transitiva | eventsource-parser | 3.1.1 | Streaming, source-agnostic EventSource/Server-Sent Events parser | ssh://git@github.com/rexxars/eventsource-parser |
| npm | transitiva | execa | 9.6.1 | Process execution for humans | sindresorhus/execa |
| npm | transitiva | expect-type | 1.4.0 | Finalidade não descrita nos metadados locais. | https://github.com/mmkal/expect-type |
| npm | transitiva | express | 5.2.1 | Fast, unopinionated, minimalist web framework | expressjs/express |
| npm | transitiva | express-rate-limit | 8.7.0 | Basic IP rate-limiting middleware for Express. Use to limit repeated requests to public APIs and/or endpoints such as password reset. | https://github.com/express-rate-limit/express-rate-limit |
| npm | transitiva | fast-deep-equal | 3.1.3 | Fast deep equal | https://github.com/epoberezkin/fast-deep-equal |
| npm | transitiva | fast-glob | 3.3.1 | It's a very fast and efficient glob library for Node.js | mrmlnc/fast-glob |
| npm | transitiva | fast-json-stable-stringify | 2.1.0 | deterministic `JSON.stringify()` - a faster version of substack's json-stable-strigify without jsonify | git://github.com/epoberezkin/fast-json-stable-stringify |
| npm | transitiva | fast-levenshtein | 2.0.6 | Efficient implementation of Levenshtein algorithm  with locale-specific collator support. | https://github.com/hiddentao/fast-levenshtein |
| npm | transitiva | fast-uri | 3.1.7 | Dependency-free RFC 3986 URI toolbox | https://github.com/fastify/fast-uri |
| npm | transitiva | fastq | 1.20.3 | Fast, in memory work queue | https://github.com/mcollina/fastq |
| npm | transitiva | figures | 6.1.0 | Unicode symbols with fallbacks for older terminals | sindresorhus/figures |
| npm | transitiva | file-entry-cache | 8.0.0 | Super simple cache for file metadata, useful for process that work o a given series of files and that only need to repeat the job on the changed ones since the previous run of the process | jaredwray/file-entry-cache |
| npm | transitiva | fill-range | 7.1.1 | Fill in a range of numbers or letters, optionally passing an increment or `step` to use, or create a regex-compatible range with `options.toRegex` | jonschlinkert/fill-range |
| npm | transitiva | finalhandler | 2.1.1 | Node.js final http responder | pillarjs/finalhandler |
| npm | transitiva | find-up | 5.0.0 | Find a file or directory by walking up parent directories | sindresorhus/find-up |
| npm | transitiva | flat-cache | 4.0.1 | A stupidly simple key/value storage using files to persist some data | jaredwray/flat-cache |
| npm | transitiva | flatted | 3.4.4 | A super light and fast circular JSON parser. | https://github.com/WebReflection/flatted |
| npm | transitiva | for-each | 0.3.5 | A better forEach | https://github.com/Raynos/for-each |
| npm | transitiva | forwarded | 0.2.0 | Parse HTTP X-Forwarded-For header | jshttp/forwarded |
| npm | transitiva | fresh | 2.0.0 | HTTP response freshness testing | jshttp/fresh |
| npm | transitiva | fs-extra | 11.4.0 | fs-extra contains methods that aren't included in the vanilla Node.js fs package. Such as recursive mkdir, copy, and remove. | https://github.com/jprichardson/node-fs-extra |
| npm | transitiva | fsevents | 2.3.3 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | function-bind | 1.1.2 | Implementation of Function.prototype.bind | https://github.com/Raynos/function-bind |
| npm | transitiva | function.prototype.name | 1.2.0 | An ES2015 spec-compliant `Function.prototype.name` shim | git://github.com/es-shims/Function.prototype.name |
| npm | transitiva | functions-have-names | 1.2.3 | Does this JS environment support the `name` property on functions? | https://github.com/inspect-js/functions-have-names |
| npm | transitiva | fuzzysort | 3.1.0 | Fast SublimeText-like fuzzy search for JavaScript | https://github.com/farzher/fuzzysort |
| npm | transitiva | generator-function | 2.0.1 | A function that returns the normally hidden `GeneratorFunction` constructor | https://github.com/TimothyGu/generator-function |
| npm | transitiva | gensync | 1.0.0-beta.2 | Allows users to use generators in order to write common functions that can be both sync or async. | https://github.com/loganfsmyth/gensync |
| npm | transitiva | get-east-asian-width | 1.6.0 | Determine the East Asian Width of a Unicode character | sindresorhus/get-east-asian-width |
| npm | transitiva | get-intrinsic | 1.3.0 | Get and robustly cache all JS language-level intrinsics at first require time | https://github.com/ljharb/get-intrinsic |
| npm | transitiva | get-own-enumerable-keys | 1.0.0 | Like `Object.keys()` but also includes symbols | sindresorhus/get-own-enumerable-keys |
| npm | transitiva | get-proto | 1.0.1 | Robustly get the [[Prototype]] of an object | https://github.com/ljharb/get-proto |
| npm | transitiva | get-stream | 9.0.1 | Get a stream as a string, Buffer, ArrayBuffer or array | sindresorhus/get-stream |
| npm | transitiva | get-symbol-description | 1.1.0 | Gets the description of a Symbol. Handles `Symbol()` vs `Symbol('')` properly when possible. | https://github.com/inspect-js/get-symbol-description |
| npm | transitiva | get-tsconfig | 4.14.3 | Find and parse the tsconfig.json file from a directory path | privatenumber/get-tsconfig |
| npm | transitiva | glob-parent | 6.0.2 | Extract the non-magic parent path from a glob string. | gulpjs/glob-parent |
| npm | transitiva | globals | 14.0.0 | Global identifiers from different JavaScript environments | sindresorhus/globals |
| npm | transitiva | globalthis | 1.0.4 | ECMAScript spec-compliant polyfill/shim for `globalThis` | git://github.com/ljharb/System.global |
| npm | transitiva | globrex | 0.1.2 | Glob to regular expression with support for extended globs | https://github.com/terkelg/globrex |
| npm | transitiva | gopd | 1.2.0 | `Object.getOwnPropertyDescriptor`, but accounts for IE's broken implementation. | https://github.com/ljharb/gopd |
| npm | transitiva | graceful-fs | 4.2.11 | A drop-in replacement for fs, making various improvements. | https://github.com/isaacs/node-graceful-fs |
| npm | transitiva | has-bigints | 1.1.0 | Determine if the JS environment has BigInt support. | https://github.com/ljharb/has-bigints |
| npm | transitiva | has-flag | 4.0.0 | Check if argv has a specific flag | sindresorhus/has-flag |
| npm | transitiva | has-property-descriptors | 1.0.2 | Does the environment have full property descriptor support? Handles IE 8's broken defineProperty/gOPD. | https://github.com/inspect-js/has-property-descriptors |
| npm | transitiva | has-proto | 1.2.0 | Does this environment have the ability to get the [[Prototype]] of an object on creation with `__proto__`? | https://github.com/inspect-js/has-proto |
| npm | transitiva | has-symbols | 1.1.0 | Determine if the JS environment has Symbol support. Supports spec, or shams. | git://github.com/inspect-js/has-symbols |
| npm | transitiva | has-tostringtag | 1.0.2 | Determine if the JS environment has `Symbol.toStringTag` support. Supports spec, or shams. | https://github.com/inspect-js/has-tostringtag |
| npm | transitiva | hasown | 2.0.4 | A robust, ES3 compatible, "has own property" predicate. | https://github.com/inspect-js/hasOwn |
| npm | transitiva | hermes-estree | 0.25.1 | Flow types for the Flow-ESTree spec produced by the hermes parser | git@github.com:facebook/hermes |
| npm | transitiva | hermes-parser | 0.25.1 | A JavaScript parser built from the Hermes engine | git@github.com:facebook/hermes |
| npm | transitiva | hono | 4.13.7 | Web framework built on Web Standards | https://github.com/honojs/hono |
| npm | transitiva | html-encoding-sniffer | 6.0.0 | Sniff the encoding from a HTML byte stream | https://github.com/jsdom/html-encoding-sniffer |
| npm | transitiva | http-errors | 2.0.1 | Create HTTP error objects | jshttp/http-errors |
| npm | transitiva | human-signals | 8.0.1 | Human-friendly process signals | https://github.com/ehmicky/human-signals |
| npm | transitiva | iconv-lite | 0.7.3 | Convert character encodings in pure javascript. | https://github.com/pillarjs/iconv-lite |
| npm | transitiva | ignore | 5.3.2 | Ignore is a manager and filter for .gitignore rules, the one used by eslint, gitbook and many others. | git@github.com:kaelzhang/node-ignore |
| npm | transitiva | import-fresh | 3.3.1 | Import a module while bypassing the cache | sindresorhus/import-fresh |
| npm | transitiva | imurmurhash | 0.1.4 | An incremental implementation of MurmurHash3 | https://github.com/jensyt/imurmurhash-js |
| npm | transitiva | indent-string | 4.0.0 | Indent each line in a string | sindresorhus/indent-string |
| npm | transitiva | inherits | 2.0.4 | Browser-friendly inheritance fully compatible with standard node.js inherits() | git://github.com/isaacs/inherits |
| npm | transitiva | internal-slot | 1.1.0 | ES spec-like internal slots | https://github.com/ljharb/internal-slot |
| npm | transitiva | ip-address | 10.7.0 | A library for parsing IPv4 and IPv6 IP addresses in node and the browser. | https://github.com/beaugunderson/ip-address |
| npm | transitiva | ipaddr.js | 1.9.1 | A library for manipulating IPv4 and IPv6 addresses in JavaScript. | git://github.com/whitequark/ipaddr.js |
| npm | transitiva | is-array-buffer | 3.0.5 | Is this value a JS ArrayBuffer? | https://github.com/inspect-js/is-array-buffer |
| npm | transitiva | is-arrayish | 0.2.1 | Determines if an object can be used as an array | https://github.com/qix-/node-is-arrayish |
| npm | transitiva | is-async-function | 2.1.1 | Determine if a function is a native async function. | git://github.com/inspect-js/is-async-function |
| npm | transitiva | is-bigint | 1.1.0 | Is this value an ES BigInt? | https://github.com/inspect-js/is-bigint |
| npm | transitiva | is-boolean-object | 1.2.2 | Is this value a JS Boolean? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | git://github.com/inspect-js/is-boolean-object |
| npm | transitiva | is-bun-module | 2.0.0 | Is this specifier a Bun core module or supported Node one? | https://github.com/SunsetTechuila/is-bun-module |
| npm | transitiva | is-callable | 1.2.7 | Is this JS value callable? Works with Functions and GeneratorFunctions, despite ES6 @@toStringTag. | git://github.com/inspect-js/is-callable |
| npm | transitiva | is-core-module | 2.16.2 | Is this specifier a node.js core module? | https://github.com/inspect-js/is-core-module |
| npm | transitiva | is-data-view | 1.0.2 | Is this value a JS DataView? This module works cross-realm/iframe, does not depend on `instanceof` or mutable properties, and despite ES6 Symbol.toStringTag. | https://github.com/inspect-js/is-data-view |
| npm | transitiva | is-date-object | 1.1.0 | Is this value a JS Date object? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | git://github.com/inspect-js/is-date-object |
| npm | transitiva | is-docker | 3.0.0 | Check if the process is running inside a Docker container | sindresorhus/is-docker |
| npm | transitiva | is-document.all | 1.0.0 | Is this value `document.all`, i.e. an object with the [[IsHTMLDDA]] internal slot? | https://github.com/inspect-js/is-document.all |
| npm | transitiva | is-extglob | 2.1.1 | Returns true if a string has an extglob. | jonschlinkert/is-extglob |
| npm | transitiva | is-finalizationregistry | 1.1.1 | Is this value a JS FinalizationRegistry? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-finalizationregistry |
| npm | transitiva | is-generator-function | 1.1.2 | Determine if a function is a native generator function. | git://github.com/inspect-js/is-generator-function |
| npm | transitiva | is-glob | 4.0.3 | Returns `true` if the given string looks like a glob pattern or an extglob pattern. This makes it easy to create code that only uses external modules like node-glob when necessary, resulting in much faster code execution and initialization time, and a better user experience. | micromatch/is-glob |
| npm | transitiva | is-in-ssh | 1.0.0 | Check if the process is running in an SSH session | sindresorhus/is-in-ssh |
| npm | transitiva | is-inside-container | 1.0.0 | Check if the process is running inside a container (Docker/Podman) | sindresorhus/is-inside-container |
| npm | transitiva | is-interactive | 2.0.0 | Check if stdout or stderr is interactive | sindresorhus/is-interactive |
| npm | transitiva | is-map | 2.0.3 | Is this value a JS Map? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-map |
| npm | transitiva | is-negative-zero | 2.0.3 | Is this value negative zero? === will lie to you | git://github.com/inspect-js/is-negative-zero |
| npm | transitiva | is-number | 7.0.0 | Returns true if a number or string value is a finite number. Useful for regex matches, parsing, user input, etc. | jonschlinkert/is-number |
| npm | transitiva | is-number-object | 1.1.1 | Is this value a JS Number object? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | git://github.com/inspect-js/is-number-object |
| npm | transitiva | is-obj | 2.0.0 | Check if a value is an object | sindresorhus/is-obj |
| npm | transitiva | is-plain-obj | 4.1.0 | Check if a value is a plain object | sindresorhus/is-plain-obj |
| npm | transitiva | is-potential-custom-element-name | 1.0.1 | Check whether a given string matches the `PotentialCustomElementName` production as defined in the HTML Standard. | https://github.com/mathiasbynens/is-potential-custom-element-name |
| npm | transitiva | is-promise | 4.0.0 | Test whether an object looks like a promises-a+ promise | https://github.com/then/is-promise |
| npm | transitiva | is-regex | 1.2.1 | Is this value a JS regex? Works cross-realm/iframe, and despite ES6 @@toStringTag | git://github.com/inspect-js/is-regex |
| npm | transitiva | is-regexp | 3.1.0 | Check if a value is a regular expression | sindresorhus/is-regexp |
| npm | transitiva | is-set | 2.0.3 | Is this value a JS Set? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-set |
| npm | transitiva | is-shared-array-buffer | 1.0.4 | Is this value a JS SharedArrayBuffer? | https://github.com/inspect-js/is-shared-array-buffer |
| npm | transitiva | is-stream | 4.0.1 | Check if something is a Node.js stream | sindresorhus/is-stream |
| npm | transitiva | is-string | 1.1.1 | Is this value a JS String object or primitive? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | git://github.com/inspect-js/is-string |
| npm | transitiva | is-symbol | 1.1.1 | Determine if a value is an ES6 Symbol or not. | git://github.com/inspect-js/is-symbol |
| npm | transitiva | is-typed-array | 1.1.15 | Is this value a JS Typed Array? This module works cross-realm/iframe, does not depend on `instanceof` or mutable properties, and despite ES6 Symbol.toStringTag. | git://github.com/inspect-js/is-typed-array |
| npm | transitiva | is-unicode-supported | 2.1.0 | Detect whether the terminal supports Unicode | sindresorhus/is-unicode-supported |
| npm | transitiva | is-weakmap | 2.0.2 | Is this value a JS WeakMap? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-weakmap |
| npm | transitiva | is-weakref | 1.1.1 | Is this value a JS WeakRef? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-weakref |
| npm | transitiva | is-weakset | 2.0.4 | Is this value a JS WeakSet? This module works cross-realm/iframe, and despite ES6 @@toStringTag. | https://github.com/inspect-js/is-weakset |
| npm | transitiva | is-wsl | 3.1.1 | Check if the process is running inside Windows Subsystem for Linux (Bash on Windows) | sindresorhus/is-wsl |
| npm | transitiva | isarray | 2.0.5 | Array#isArray for older browsers | git://github.com/juliangruber/isarray |
| npm | transitiva | isexe | 2.0.0 | Minimal module to check if a file is executable. | https://github.com/isaacs/isexe |
| npm | transitiva | iterator.prototype | 1.1.5 | `Iterator.prototype`, or a shared object to use. | https://github.com/ljharb/Iterator.prototype |
| npm | transitiva | jiti | 2.7.0 | Runtime typescript and ESM support for Node.js | unjs/jiti |
| npm | transitiva | jose | 6.2.12 | JWA, JWS, JWE, JWT, JWK, JWKS for Node.js, Browser, Cloudflare Workers, Deno, Bun, and other Web-interoperable runtimes | panva/jose |
| npm | transitiva | js-tokens | 4.0.0 | A regex that tokenizes JavaScript. | lydell/js-tokens |
| npm | transitiva | js-yaml | 4.3.2 | YAML 1.2 parser and serializer | nodeca/js-yaml |
| npm | transitiva | jsdom | 30.0.1 | A JavaScript implementation of many web standards | https://github.com/jsdom/jsdom |
| npm | transitiva | jsesc | 3.1.0 | Given some data, jsesc returns the shortest possible stringified & ASCII-safe representation of that data. | https://github.com/mathiasbynens/jsesc |
| npm | transitiva | json-buffer | 3.0.1 | JSON parse & stringify that supports binary via bops & base64 | git://github.com/dominictarr/json-buffer |
| npm | transitiva | json-parse-even-better-errors | 2.3.1 | JSON.parse with context information on error | https://github.com/npm/json-parse-even-better-errors |
| npm | transitiva | json-schema-traverse | 0.4.1 | Traverse JSON Schema passing each schema object to callback | https://github.com/epoberezkin/json-schema-traverse |
| npm | transitiva | json-schema-typed | 8.0.2 | JSON Schema TypeScript definitions with complete inline documentation. | https://github.com/RemyRylan/json-schema-typed |
| npm | transitiva | json-stable-stringify-without-jsonify | 1.0.1 | deterministic JSON.stringify() with custom sorting to get deterministic hashes from stringified results, with no public domain dependencies | git://github.com/samn/json-stable-stringify |
| npm | transitiva | json5 | 2.2.3 | JSON for Humans | https://github.com/json5/json5 |
| npm | transitiva | jsonfile | 6.2.1 | Easily read/write JSON files. | git@github.com:jprichardson/node-jsonfile |
| npm | transitiva | jsx-ast-utils | 3.3.5 | AST utility module for statically analyzing JSX | https://github.com/jsx-eslint/jsx-ast-utils |
| npm | transitiva | keyv | 4.5.4 | Simple key-value storage with support for multiple backends | https://github.com/jaredwray/keyv |
| npm | transitiva | kleur | 4.1.5 | The fastest Node.js library for formatting terminal text with ANSI colors~! | lukeed/kleur |
| npm | transitiva | language-subtag-registry | 0.3.23 | Full BCP 47 language subtag data from the official IANA repository, in JSON format with multiple indices. | https://github.com/mattcg/language-subtag-registry |
| npm | transitiva | language-tags | 1.0.9 | Work with IANA language tags. | git://github.com/mattcg/language-tags |
| npm | transitiva | levn | 0.4.1 | Light ECMAScript (JavaScript) Value Notation - human written, concise, typed, flexible | git://github.com/gkz/levn |
| npm | transitiva | lightningcss | 1.32.0 | A CSS parser, transformer, and minifier written in Rust | https://github.com/parcel-bundler/lightningcss |
| npm | transitiva | lightningcss-android-arm64 | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-darwin-arm64 | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-darwin-x64 | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-freebsd-x64 | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm-gnueabihf | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm64-gnu | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm64-musl | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-x64-gnu | 1.32.0 | A CSS parser, transformer, and minifier written in Rust | https://github.com/parcel-bundler/lightningcss |
| npm | transitiva | lightningcss-linux-x64-musl | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-win32-arm64-msvc | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-win32-x64-msvc | 1.32.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lines-and-columns | 1.2.4 | Maps lines and columns to character offsets and back. | https://github.com/eventualbuddha/lines-and-columns |
| npm | transitiva | locate-path | 6.0.0 | Get the first path that exists on disk of multiple paths | sindresorhus/locate-path |
| npm | transitiva | lodash.merge | 4.6.2 | The Lodash method `_.merge` exported as a module. | lodash/lodash |
| npm | transitiva | log-symbols | 6.0.0 | Colored symbols for various log levels. Example: `✔︎ Success` | sindresorhus/log-symbols |
| npm | transitiva | chalk | 5.6.2 | Terminal string styling done right | chalk/chalk |
| npm | transitiva | is-unicode-supported | 1.3.0 | Detect whether the terminal supports Unicode | sindresorhus/is-unicode-supported |
| npm | transitiva | loose-envify | 1.4.0 | Fast (and loose) selective `process.env` replacer using js-tokens instead of an AST | git://github.com/zertosh/loose-envify |
| npm | transitiva | lru-cache | 5.1.1 | A cache object that deletes the least-recently-used items. | git://github.com/isaacs/node-lru-cache |
| npm | transitiva | lucide-react | 1.41.0 | A Lucide icon library package for React applications. | https://github.com/lucide-icons/lucide |
| npm | transitiva | lz-string | 1.5.0 | LZ-based compression algorithm | https://github.com/pieroxy/lz-string |
| npm | transitiva | magic-string | 0.30.21 | Modify strings, generate sourcemaps | https://github.com/Rich-Harris/magic-string |
| npm | transitiva | math-intrinsics | 1.1.0 | ES Math-related intrinsics and helpers, robustly cached. | https://github.com/es-shims/math-intrinsics |
| npm | transitiva | mdn-data | 2.27.1 | Open Web data by the Mozilla Developer Network | https://github.com/mdn/data |
| npm | transitiva | media-typer | 1.1.1 | Simple RFC 6838 media type parser and formatter | jshttp/media-typer |
| npm | transitiva | merge-descriptors | 2.0.0 | Merge objects using their property descriptors | sindresorhus/merge-descriptors |
| npm | transitiva | merge-stream | 2.0.0 | Create a stream that emits events from multiple other streams | grncdr/merge-stream |
| npm | transitiva | merge2 | 1.4.1 | Merge multiple streams into one stream in sequence or parallel. | git@github.com:teambition/merge2 |
| npm | transitiva | micromatch | 4.0.8 | Glob matching for javascript/node.js. A replacement and faster alternative to minimatch and multimatch. | micromatch/micromatch |
| npm | transitiva | mime-db | 1.54.0 | Media Type Database | jshttp/mime-db |
| npm | transitiva | mime-types | 3.0.2 | The ultimate javascript content-type utility. | jshttp/mime-types |
| npm | transitiva | mimic-fn | 3.1.0 | Make a function mimic another one | sindresorhus/mimic-fn |
| npm | transitiva | mimic-function | 5.0.1 | Make a function mimic another one | sindresorhus/mimic-function |
| npm | transitiva | min-indent | 1.0.1 | Get the shortest leading whitespace from lines in a string | https://github.com/thejameskyle/min-indent |
| npm | transitiva | minimatch | 3.1.5 | a glob matcher in javascript | git://github.com/isaacs/minimatch |
| npm | transitiva | minimist | 1.2.8 | parse argument options | git://github.com/minimistjs/minimist |
| npm | transitiva | ms | 2.1.3 | Tiny millisecond conversion utility | vercel/ms |
| npm | transitiva | nanoid | 3.3.18 | A tiny (116 bytes), secure URL-friendly unique string ID generator | ai/nanoid |
| npm | transitiva | napi-postinstall | 0.3.4 | The `postinstall` script helper for handling native bindings in legacy `npm` versions | https://github.com/un-ts/napi-postinstall |
| npm | transitiva | natural-compare | 1.4.0 | Compare strings containing a mix of letters and numbers in the way a human being would in sort order. | git://github.com/litejs/natural-compare-lite |
| npm | transitiva | negotiator | 1.1.0 | HTTP content negotiation | jshttp/negotiator |
| npm | transitiva | next | 16.3.4 | The React Framework | vercel/next.js |
| npm | transitiva | postcss | 8.5.23 | Tool for transforming styles with JS plugins | postcss/postcss |
| npm | transitiva | node-exports-info | 1.6.2 | Info about node `exports` field support: version ranges, categories, etc. | https://github.com/inspect-js/node-exports-info |
| npm | transitiva | node-releases | 2.0.54 | Node.js releases data | https://github.com/chicoxyzzy/node-releases |
| npm | transitiva | npm-run-path | 6.0.0 | Get your PATH prepended with locally installed binaries | sindresorhus/npm-run-path |
| npm | transitiva | path-key | 4.0.0 | Get the PATH environment variable key cross-platform | sindresorhus/path-key |
| npm | transitiva | object-assign | 4.1.1 | ES2015 `Object.assign()` ponyfill | sindresorhus/object-assign |
| npm | transitiva | object-inspect | 1.13.4 | string representations of objects in node and the browser | git://github.com/inspect-js/object-inspect |
| npm | transitiva | object-keys | 1.1.1 | An Object.keys replacement, in case Object.keys is not available. From https://github.com/es-shims/es5-shim | git://github.com/ljharb/object-keys |
| npm | transitiva | object-treeify | 1.1.33 | Stringify Object as tree structure | https://github.com/blackflux/object-treeify |
| npm | transitiva | object.assign | 4.1.7 | ES6 spec-compliant Object.assign shim. From https://github.com/es-shims/es6-shim | git://github.com/ljharb/object.assign |
| npm | transitiva | object.entries | 1.1.9 | ES2017 spec-compliant Object.entries shim. | git://github.com/es-shims/Object.entries |
| npm | transitiva | object.fromentries | 2.0.8 | ES proposal-spec-compliant Object.fromEntries shim. | git://github.com/es-shims/Object.fromEntries |
| npm | transitiva | object.groupby | 1.0.3 | An ESnext spec-compliant `Object.groupBy` shim/polyfill/replacement that works as far down as ES3. | https://github.com/es-shims/Object.groupBy |
| npm | transitiva | object.values | 1.2.1 | ES2017 spec-compliant Object.values shim. | git://github.com/es-shims/Object.values |
| npm | transitiva | obug | 2.1.4 | A lightweight JavaScript debugging utility, forked from debug, featuring TypeScript and ESM support. | https://github.com/sxzz/obug |
| npm | transitiva | on-finished | 2.4.1 | Execute a callback when a request closes, finishes, or errors | jshttp/on-finished |
| npm | transitiva | once | 1.4.0 | Run a function exactly one time | git://github.com/isaacs/once |
| npm | transitiva | onetime | 5.1.2 | Ensure a function is only called once | sindresorhus/onetime |
| npm | transitiva | mimic-fn | 2.1.0 | Make a function mimic another one | sindresorhus/mimic-fn |
| npm | transitiva | open | 11.0.2 | Open stuff like URLs, files, executables. Cross-platform. | sindresorhus/open |
| npm | transitiva | optionator | 0.9.4 | option parsing and help generation | git://github.com/gkz/optionator |
| npm | transitiva | ora | 8.2.0 | Elegant terminal spinner | sindresorhus/ora |
| npm | transitiva | ansi-regex | 6.3.0 | Regular expression for matching ANSI escape codes | chalk/ansi-regex |
| npm | transitiva | strip-ansi | 7.2.0 | Strip ANSI escape codes from a string | chalk/strip-ansi |
| npm | transitiva | own-keys | 1.0.2 | Robustly get an object's own property keys (strings and symbols), including non-enumerables when possible | https://github.com/ljharb/own-keys |
| npm | transitiva | p-limit | 3.1.0 | Run multiple promise-returning & async functions with limited concurrency | sindresorhus/p-limit |
| npm | transitiva | p-locate | 5.0.0 | Get the first fulfilled promise that satisfies the provided testing function | sindresorhus/p-locate |
| npm | transitiva | p-try | 2.2.0 | `Start a promise chain | sindresorhus/p-try |
| npm | transitiva | parent-module | 1.0.1 | Get the path of the parent module | sindresorhus/parent-module |
| npm | transitiva | parse-json | 5.2.0 | Parse JSON with more helpful errors | sindresorhus/parse-json |
| npm | transitiva | parse-ms | 4.0.0 | Parse milliseconds into an object | sindresorhus/parse-ms |
| npm | transitiva | parse5 | 8.0.1 | HTML parser and serializer. | git://github.com/inikulin/parse5 |
| npm | transitiva | parseurl | 1.3.3 | parse a url with memoization | pillarjs/parseurl |
| npm | transitiva | path-browserify | 1.0.1 | the path module from node core for browsers | git://github.com/browserify/path-browserify |
| npm | transitiva | path-exists | 4.0.0 | Check if a path exists | sindresorhus/path-exists |
| npm | transitiva | path-key | 3.1.1 | Get the PATH environment variable key cross-platform | sindresorhus/path-key |
| npm | transitiva | path-parse | 1.0.7 | Node.js path.parse() ponyfill | https://github.com/jbgutierrez/path-parse |
| npm | transitiva | path-to-regexp | 8.4.2 | Express style path to RegExp utility | https://github.com/pillarjs/path-to-regexp |
| npm | transitiva | picocolors | 1.1.1 | The tiniest and the fastest library for terminal output formatting with ANSI colors | alexeyraspopov/picocolors |
| npm | transitiva | picomatch | 2.3.2 | Blazing fast and accurate glob matcher written in JavaScript, with no dependencies and full support for standard and extended Bash glob features, including braces, extglobs, POSIX brackets, and regular expressions. | micromatch/picomatch |
| npm | transitiva | pkce-challenge | 5.0.1 | Generate or verify a Proof Key for Code Exchange (PKCE) challenge pair | https://github.com/crouchcd/pkce-challenge |
| npm | transitiva | pkg-up | 3.1.0 | Find the closest package.json file | sindresorhus/pkg-up |
| npm | transitiva | find-up | 3.0.0 | Find a file or directory by walking up parent directories | sindresorhus/find-up |
| npm | transitiva | locate-path | 3.0.0 | Get the first path that exists on disk of multiple paths | sindresorhus/locate-path |
| npm | transitiva | p-limit | 2.3.0 | Run multiple promise-returning & async functions with limited concurrency | sindresorhus/p-limit |
| npm | transitiva | p-locate | 3.0.0 | Get the first fulfilled promise that satisfies the provided testing function | sindresorhus/p-locate |
| npm | transitiva | path-exists | 3.0.0 | Check if a path exists | sindresorhus/path-exists |
| npm | transitiva | possible-typed-array-names | 1.1.0 | A simple list of possible Typed Array names. | https://github.com/ljharb/possible-typed-array-names |
| npm | transitiva | postcss | 8.5.28 | Tool for transforming styles with JS plugins | postcss/postcss |
| npm | transitiva | postcss-selector-parser | 7.1.6 | Selector parser with built in methods for working with selector strings. | https://github.com/postcss/postcss-selector-parser |
| npm | transitiva | powershell-utils | 0.2.1 | Utilities for executing PowerShell commands | sindresorhus/powershell-utils |
| npm | transitiva | prelude-ls | 1.2.1 | prelude.ls is a functionally oriented utility library. It is powerful and flexible. Almost all of its functions are curried. It is written in, and is the recommended base library for, LiveScript. | git://github.com/gkz/prelude-ls |
| npm | transitiva | pretty-format | 27.5.1 | Stringify any JavaScript value. | https://github.com/facebook/jest |
| npm | transitiva | ansi-styles | 5.2.0 | ANSI escape codes for styling strings in the terminal | chalk/ansi-styles |
| npm | transitiva | react-is | 17.0.2 | Brand checking of React Elements. | https://github.com/facebook/react |
| npm | transitiva | pretty-ms | 9.3.1 | Convert milliseconds to a human readable string: `1337000000` → `15d 11h 23m 20s` | sindresorhus/pretty-ms |
| npm | transitiva | prompts | 2.4.2 | Lightweight, beautiful and user-friendly prompts | terkelg/prompts |
| npm | transitiva | kleur | 3.0.3 | The fastest Node.js library for formatting terminal text with ANSI colors~! | lukeed/kleur |
| npm | transitiva | prop-types | 15.8.1 | Runtime type checking for React props and similar objects. | facebook/prop-types |
| npm | transitiva | proxy-addr | 2.0.7 | Determine address of proxied request | jshttp/proxy-addr |
| npm | transitiva | punycode | 2.3.1 | A robust Punycode converter that fully complies to RFC 3492 and RFC 5891, and works on nearly all JavaScript platforms. | https://github.com/mathiasbynens/punycode.js |
| npm | transitiva | qs | 6.16.0 | A querystring parser that supports nesting and arrays, with a depth limit | https://github.com/ljharb/qs |
| npm | transitiva | queue-microtask | 1.2.3 | fast, tiny `queueMicrotask` shim for modern engines | git://github.com/feross/queue-microtask |
| npm | transitiva | range-parser | 1.3.0 | Range header field string parser | jshttp/range-parser |
| npm | transitiva | raw-body | 3.0.2 | Get and validate the raw body of a readable stream. | stream-utils/raw-body |
| npm | transitiva | react | 19.2.8 | React is a JavaScript library for building user interfaces. | https://github.com/react/react |
| npm | transitiva | react-dom | 19.2.8 | React package for working with the DOM. | https://github.com/react/react |
| npm | transitiva | react-is | 16.13.1 | Brand checking of React Elements. | https://github.com/facebook/react |
| npm | transitiva | recast | 0.23.21 | JavaScript syntax tree transformer, nondestructive pretty-printer, and automatic source map generator | git://github.com/benjamn/recast |
| npm | transitiva | redent | 3.0.0 | Strip redundant indentation and indent the string | sindresorhus/redent |
| npm | transitiva | reflect.getprototypeof | 1.0.10 | An ES2015 mostly-spec-compliant `Reflect.getPrototypeOf` sham/polyfill/replacement that works in as many engines as possible | https://github.com/es-shims/Reflect.getPrototypeOf |
| npm | transitiva | regexp.prototype.flags | 1.5.4 | ES6 spec-compliant RegExp.prototype.flags shim. | git://github.com/es-shims/RegExp.prototype.flags |
| npm | transitiva | require-from-string | 2.0.2 | Require module from string | floatdrop/require-from-string |
| npm | transitiva | reselect | 5.3.0 | Selectors for Redux. | https://github.com/reduxjs/reselect |
| npm | transitiva | resolve | 2.0.0-next.7 | resolve like require.resolve() on behalf of files asynchronously and synchronously | ssh://github.com/browserify/resolve |
| npm | transitiva | resolve-from | 4.0.0 | Resolve the path of a module like `require.resolve()` but from a given path | sindresorhus/resolve-from |
| npm | transitiva | resolve-pkg-maps | 1.0.0 | Resolve package.json exports & imports maps | privatenumber/resolve-pkg-maps |
| npm | transitiva | restore-cursor | 5.1.0 | Gracefully restore the CLI cursor on exit | sindresorhus/restore-cursor |
| npm | transitiva | onetime | 7.0.0 | Ensure a function is only called once | sindresorhus/onetime |
| npm | transitiva | reusify | 1.1.0 | Reuse objects and functions with style | https://github.com/mcollina/reusify |
| npm | transitiva | rolldown | 1.2.7 | Fast JavaScript/TypeScript bundler in Rust with Rollup-compatible API. | https://github.com/rolldown/rolldown |
| npm | transitiva | router | 2.2.0 | Simple middleware-style router | pillarjs/router |
| npm | transitiva | run-applescript | 7.1.0 | Run AppleScript and get the result | sindresorhus/run-applescript |
| npm | transitiva | run-parallel | 1.2.0 | Run an array of functions in parallel | git://github.com/feross/run-parallel |
| npm | transitiva | safe-array-concat | 1.1.4 | `Array.prototype.concat`, but made safe by ignoring Symbol.isConcatSpreadable | https://github.com/ljharb/safe-array-concat |
| npm | transitiva | safe-push-apply | 1.0.0 | Push an array of items into an array, while being robust against prototype modification | https://github.com/ljharb/safe-push-apply |
| npm | transitiva | safe-regex-test | 1.1.0 | Give a regex, get a robust predicate function that tests it against a string. | https://github.com/ljharb/safe-regex-test |
| npm | transitiva | safer-buffer | 2.1.2 | Modern Buffer API polyfill without footguns | https://github.com/ChALkeR/safer-buffer |
| npm | transitiva | saxes | 6.0.0 | An evented streaming XML parser in JavaScript | https://github.com/lddubeau/saxes |
| npm | transitiva | scheduler | 0.27.0 | Cooperative scheduler for the browser environment. | https://github.com/facebook/react |
| npm | transitiva | semver | 6.3.1 | The semantic version parser used by npm. | https://github.com/npm/node-semver |
| npm | transitiva | send | 1.2.1 | Better streaming static file server with Range and conditional-GET support | pillarjs/send |
| npm | transitiva | serve-static | 2.2.1 | Serve static files | expressjs/serve-static |
| npm | transitiva | set-function-length | 1.2.2 | Set a function's length property | https://github.com/ljharb/set-function-length |
| npm | transitiva | set-function-name | 2.0.2 | Set a function's name property | https://github.com/ljharb/set-function-name |
| npm | transitiva | set-proto | 1.0.0 | Robustly set the [[Prototype]] of an object | https://github.com/ljharb/set-proto |
| npm | transitiva | setprototypeof | 1.2.0 | A small polyfill for Object.setprototypeof | https://github.com/wesleytodd/setprototypeof |
| npm | transitiva | shadcn | 4.21.0 | Add components to your apps. | https://github.com/shadcn-ui/ui |
| npm | transitiva | tsconfig-paths | 4.2.0 | Load node modules according to tsconfig paths, in run-time or via API. | https://github.com/dividab/tsconfig-paths |
| npm | transitiva | zod | 3.25.76 | TypeScript-first schema declaration and validation library with static type inference | https://github.com/colinhacks/zod |
| npm | transitiva | sharp | 0.35.4 | High performance Node.js image processing, the fastest module to resize JPEG, PNG, WebP, GIF, AVIF and TIFF images | https://github.com/lovell/sharp |
| npm | transitiva | shebang-command | 2.0.0 | Get the command from a shebang | kevva/shebang-command |
| npm | transitiva | shebang-regex | 3.0.0 | Regular expression for matching a shebang line | sindresorhus/shebang-regex |
| npm | transitiva | side-channel | 1.1.1 | Store information about any JS value in a side channel. Uses WeakMap if available. | https://github.com/ljharb/side-channel |
| npm | transitiva | side-channel-list | 1.0.1 | Store information about any JS value in a side channel, using a linked list | https://github.com/ljharb/side-channel-list |
| npm | transitiva | side-channel-map | 1.0.1 | Store information about any JS value in a side channel, using a Map | https://github.com/ljharb/side-channel-map |
| npm | transitiva | side-channel-weakmap | 1.0.2 | Store information about any JS value in a side channel. Uses WeakMap if available. | https://github.com/ljharb/side-channel-weakmap |
| npm | transitiva | siginfo | 2.0.0 | Utility module to print pretty messages on SIGINFO/SIGUSR1 | https://github.com/emilbayes/siginfo |
| npm | transitiva | signal-exit | 4.1.0 | when you want to fire an event no matter how a process exits. | https://github.com/tapjs/signal-exit |
| npm | transitiva | sisteransi | 1.0.5 | ANSI escape codes for some terminal swag | https://github.com/terkelg/sisteransi |
| npm | transitiva | smart-buffer | 4.2.0 | smart-buffer is a Buffer wrapper that adds automatic read & write offset tracking, string operations, data insertions, and more. | https://github.com/JoshGlazebrook/smart-buffer |
| npm | transitiva | socks | 2.8.10 | Fully featured SOCKS proxy client supporting SOCKSv4, SOCKSv4a, and SOCKSv5. Includes Bind and Associate functionality. | https://github.com/JoshGlazebrook/socks |
| npm | transitiva | source-map | 0.6.1 | Generates and consumes source maps | http://github.com/mozilla/source-map |
| npm | transitiva | source-map-js | 1.2.1 | Generates and consumes source maps | 7rulnik/source-map-js |
| npm | transitiva | stable-hash | 0.0.5 | Stable JS value hash. | https://github.com/shuding/stable-hash |
| npm | transitiva | stackback | 0.0.2 | return list of CallSite objects from a captured stacktrace | git://github.com/shtylman/node-stackback |
| npm | transitiva | statuses | 2.0.2 | HTTP status utility | jshttp/statuses |
| npm | transitiva | std-env | 4.2.0 | Runtime agnostic JS utils | unjs/std-env |
| npm | transitiva | stdin-discarder | 0.2.2 | Discard stdin input except for Ctrl+C | sindresorhus/stdin-discarder |
| npm | transitiva | stop-iteration-iterator | 1.1.0 | Firefox 17-26 iterators throw a StopIteration object to indicate "done". This normalizes it. | https://github.com/ljharb/stop-iteration-iterator |
| npm | transitiva | string-width | 7.2.0 | Get the visual width of a string - the number of columns required to display it | sindresorhus/string-width |
| npm | transitiva | emoji-regex | 10.6.0 | A regular expression to match all Emoji-only symbols as per the Unicode Standard. | https://github.com/mathiasbynens/emoji-regex |
| npm | transitiva | string.prototype.includes | 2.0.1 | A robust & optimized `String.prototype.includes` polyfill, based on the ECMAScript 6 specification. | https://github.com/mathiasbynens/String.prototype.includes |
| npm | transitiva | string.prototype.matchall | 4.1.0 | Spec-compliant polyfill for String.prototype.matchAll | https://github.com/es-shims/String.prototype.matchAll |
| npm | transitiva | string.prototype.repeat | 1.0.0 | A robust & optimized `String.prototype.repeat` polyfill, based on the ECMAScript 6 specification. | https://github.com/mathiasbynens/String.prototype.repeat |
| npm | transitiva | string.prototype.trim | 1.2.11 | ES5 spec-compliant shim for String.prototype.trim | git://github.com/es-shims/String.prototype.trim |
| npm | transitiva | string.prototype.trimend | 1.0.10 | ES2019 spec-compliant String.prototype.trimEnd shim. | git://github.com/es-shims/String.prototype.trimEnd |
| npm | transitiva | string.prototype.trimstart | 1.0.8 | ES2019 spec-compliant String.prototype.trimStart shim. | git://github.com/es-shims/String.prototype.trimStart |
| npm | transitiva | stringify-object | 5.0.0 | Stringify an object/array like JSON.stringify just without all the double-quotes | yeoman/stringify-object |
| npm | transitiva | is-obj | 3.0.0 | Check if a value is an object | sindresorhus/is-obj |
| npm | transitiva | strip-ansi | 6.0.1 | Strip ANSI escape codes from a string | chalk/strip-ansi |
| npm | transitiva | strip-bom | 3.0.0 | Strip UTF-8 byte order mark (BOM) from a string | sindresorhus/strip-bom |
| npm | transitiva | strip-final-newline | 4.0.0 | Strip the final newline character from a string or Uint8Array | sindresorhus/strip-final-newline |
| npm | transitiva | strip-indent | 3.0.0 | Strip leading whitespace from each line in a string | sindresorhus/strip-indent |
| npm | transitiva | strip-json-comments | 3.1.1 | Strip comments from JSON. Lets you use comments in your JSON files! | sindresorhus/strip-json-comments |
| npm | transitiva | styled-jsx | 5.1.6 | Full CSS support for JSX without compromises | vercel/styled-jsx |
| npm | transitiva | supports-color | 7.2.0 | Detect whether a terminal supports color | chalk/supports-color |
| npm | transitiva | supports-preserve-symlinks-flag | 1.0.0 | Determine if the current node version supports the `--preserve-symlinks` flag. | https://github.com/inspect-js/node-supports-preserve-symlinks-flag |
| npm | transitiva | symbol-tree | 3.2.4 | Turn any collection of objects into its own efficient tree or linked list using Symbol | https://github.com/jsdom/js-symbol-tree |
| npm | transitiva | systeminformation | 5.33.8 | Advanced, lightweight system and OS information library | https://github.com/sebhildebrandt/systeminformation |
| npm | transitiva | tailwindcss | 4.3.3 | A utility-first CSS framework for rapidly building custom user interfaces. | https://github.com/tailwindlabs/tailwindcss |
| npm | transitiva | tapable | 2.3.3 | Just a little module for plugins. | http://github.com/webpack/tapable |
| npm | transitiva | tiny-invariant | 1.3.3 | A tiny invariant function | https://github.com/alexreardon/tiny-invariant |
| npm | transitiva | tinybench | 6.1.4 | 🔎 A simple, tiny and lightweight benchmarking library! | tinylibs/tinybench |
| npm | transitiva | tinyexec | 1.3.0 | A minimal library for executing processes in Node | https://github.com/tinylibs/tinyexec |
| npm | transitiva | tinyglobby | 0.2.17 | A fast and minimal alternative to globby and fast-glob | https://github.com/SuperchupuDev/tinyglobby |
| npm | transitiva | tldts | 7.4.11 | Library to work against complex domain names, subdomains and URIs. | ssh://git@github.com/remusao/tldts |
| npm | transitiva | tldts-core | 7.4.11 | tldts core primitives (internal module) | ssh://git@github.com/remusao/tldts |
| npm | transitiva | to-regex-range | 5.0.1 | Pass two numbers, get a regex-compatible source string for matching ranges. Validated against more than 2.78 million test assertions. | micromatch/to-regex-range |
| npm | transitiva | toidentifier | 1.0.1 | Convert a string of words to a JavaScript identifier | component/toidentifier |
| npm | transitiva | tough-cookie | 6.0.2 | RFC6265 Cookies and Cookie Jar for node.js | git://github.com/salesforce/tough-cookie |
| npm | transitiva | tr46 | 6.0.0 | An implementation of the Unicode UTS #46: Unicode IDNA Compatibility Processing | https://github.com/jsdom/tr46 |
| npm | transitiva | ts-api-utils | 2.5.0 | Utility functions for working with TypeScript's API. Successor to the wonderful tsutils. 🛠️️ | https://github.com/JoshuaKGoldberg/ts-api-utils |
| npm | transitiva | ts-morph | 26.0.0 | TypeScript compiler wrapper for static analysis and code manipulation. | https://github.com/dsherret/ts-morph |
| npm | transitiva | tsconfck | 3.1.6 | A utility to work with tsconfig.json without typescript | https://github.com/dominikg/tsconfck |
| npm | transitiva | tsconfig-paths | 3.15.0 | Load node modules according to tsconfig paths, in run-time or via API. | https://github.com/dividab/tsconfig-paths |
| npm | transitiva | json5 | 1.0.2 | JSON for Humans | https://github.com/json5/json5 |
| npm | transitiva | tslib | 2.8.1 | Runtime library for TypeScript helper functions | https://github.com/Microsoft/tslib |
| npm | transitiva | tw-animate-css | 1.4.0 | TailwindCSS v4.0 compatible replacement for `tailwindcss-animate`. | Wombosvideo/tw-animate-css |
| npm | transitiva | type-check | 0.4.0 | type-check allows you to check the types of JavaScript values at runtime with a Haskell like type syntax. | git://github.com/gkz/type-check |
| npm | transitiva | type-is | 2.1.0 | Infer the content-type of a request. | jshttp/type-is |
| npm | transitiva | typed-array-buffer | 1.0.3 | Get the ArrayBuffer out of a TypedArray, robustly. | https://github.com/inspect-js/typed-array-buffer |
| npm | transitiva | typed-array-byte-length | 1.0.3 | Robustly get the byte length of a Typed Array | https://github.com/inspect-js/typed-array-byte-length |
| npm | transitiva | typed-array-byte-offset | 1.0.4 | Robustly get the byte offset of a Typed Array | https://github.com/inspect-js/typed-array-byte-offset |
| npm | transitiva | typed-array-length | 1.0.8 | Robustly get the length of a Typed Array | https://github.com/inspect-js/typed-array-length |
| npm | transitiva | typescript | 5.9.3 | TypeScript is a language for application scale JavaScript development | https://github.com/microsoft/TypeScript |
| npm | transitiva | typescript-eslint | 8.69.0 | Tooling which enables you to use TypeScript with ESLint | https://github.com/typescript-eslint/typescript-eslint |
| npm | transitiva | unbox-primitive | 1.1.0 | Unbox a boxed JS primitive value. | https://github.com/ljharb/unbox-primitive |
| npm | transitiva | undici | 8.10.2 | An HTTP/1.1 client, written from scratch for Node.js | https://github.com/nodejs/undici |
| npm | transitiva | undici-types | 7.18.2 | A stand-alone types package for Undici | https://github.com/nodejs/undici |
| npm | transitiva | unicorn-magic | 0.3.0 | Some useful utilities I often need | sindresorhus/unicorn-magic |
| npm | transitiva | universalify | 2.0.1 | Make a callback- or promise-based function support both promises and callbacks. | https://github.com/RyanZim/universalify |
| npm | transitiva | unpipe | 1.0.0 | Unpipe a stream from all destinations | stream-utils/unpipe |
| npm | transitiva | unrs-resolver | 1.12.2 | UnRS Resolver Node API | https://github.com/unrs/unrs-resolver |
| npm | transitiva | update-browserslist-db | 1.3.2 | CLI tool to update caniuse-lite to refresh target browsers from Browserslist config | browserslist/update-db |
| npm | transitiva | uri-js | 4.4.1 | An RFC 3986/3987 compliant, scheme extendable URI/IRI parsing/validating/resolving library for JavaScript. | http://github.com/garycourt/uri-js |
| npm | transitiva | use-sync-external-store | 1.6.0 | Backwards compatible shim for React's useSyncExternalStore. Works with any React that supports hooks. | https://github.com/facebook/react |
| npm | transitiva | util-deprecate | 1.0.2 | The Node.js `util.deprecate()` function with browser support | git://github.com/TooTallNate/util-deprecate |
| npm | transitiva | validate-npm-package-name | 7.0.2 | Give me a string and I'll tell you if it's a valid npm package name | https://github.com/npm/validate-npm-package-name |
| npm | transitiva | vary | 1.1.2 | Manipulate the HTTP Vary header | jshttp/vary |
| npm | transitiva | vite | 8.2.2 | Native-ESM powered web dev build tool | https://github.com/vitejs/vite |
| npm | transitiva | vite-tsconfig-paths | 6.1.1 | Vite resolver for TypeScript compilerOptions.paths | aleclarson/vite-tsconfig-paths |
| npm | transitiva | lightningcss | 1.33.0 | A CSS parser, transformer, and minifier written in Rust | https://github.com/parcel-bundler/lightningcss |
| npm | transitiva | lightningcss-android-arm64 | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-darwin-arm64 | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-darwin-x64 | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-freebsd-x64 | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm-gnueabihf | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm64-gnu | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-arm64-musl | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-linux-x64-gnu | 1.33.0 | A CSS parser, transformer, and minifier written in Rust | https://github.com/parcel-bundler/lightningcss |
| npm | transitiva | lightningcss-linux-x64-musl | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-win32-arm64-msvc | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | lightningcss-win32-x64-msvc | 1.33.0 | Finalidade não descrita nos metadados locais. |  |
| npm | transitiva | vitest | 5.0.0 | Next generation testing framework powered by Vite | https://github.com/vitest-dev/vitest |
| npm | transitiva | w3c-xmlserializer | 5.0.0 | A per-spec XML serializer implementation | jsdom/w3c-xmlserializer |
| npm | transitiva | webidl-conversions | 8.0.1 | Implements the WebIDL algorithms for converting to and from JavaScript values | https://github.com/jsdom/webidl-conversions |
| npm | transitiva | whatwg-mimetype | 5.0.0 | Parses, serializes, and manipulates MIME types, according to the WHATWG MIME Sniffing Standard | jsdom/whatwg-mimetype |
| npm | transitiva | whatwg-url | 17.1.0 | An implementation of the WHATWG URL Standard's URL API and parsing machinery | https://github.com/jsdom/whatwg-url |
| npm | transitiva | which | 2.0.2 | Like which(1) unix command. Find the first instance of an executable in the PATH. | git://github.com/isaacs/node-which |
| npm | transitiva | which-boxed-primitive | 1.1.1 | Which kind of boxed JS primitive is this? | https://github.com/inspect-js/which-boxed-primitive |
| npm | transitiva | which-builtin-type | 1.2.1 | What is the type of this builtin JS value? | https://github.com/inspect-js/which-builtin-type |
| npm | transitiva | which-collection | 1.0.2 | Which kind of Collection (Map, Set, WeakMap, WeakSet) is this JavaScript value? Works cross-realm, without `instanceof`, and despite Symbol.toStringTag. | https://github.com/inspect-js/which-collection |
| npm | transitiva | which-typed-array | 1.1.22 | Which kind of Typed Array is this JavaScript value? Works cross-realm, without `instanceof`, and despite Symbol.toStringTag. | git://github.com/inspect-js/which-typed-array |
| npm | transitiva | why-is-node-running | 2.3.0 | Node is running but you don't know why? why-is-node-running is here to help you. | https://github.com/mafintosh/why-is-node-running |
| npm | transitiva | word-wrap | 1.2.5 | Wrap words to a specified length. | jonschlinkert/word-wrap |
| npm | transitiva | wrappy | 1.0.2 | Callback wrapping utility | https://github.com/npm/wrappy |
| npm | transitiva | wsl-utils | 1.0.0 | Utilities for working with Windows Subsystem for Linux (WSL) | sindresorhus/wsl-utils |
| npm | transitiva | powershell-utils | 0.1.0 | Utilities for executing PowerShell commands | sindresorhus/powershell-utils |
| npm | transitiva | xml-name-validator | 5.0.0 | Validates whether a string matches the production for an XML name or qualified name | jsdom/xml-name-validator |
| npm | transitiva | xmlchars | 2.2.0 | Utilities for determining if characters belong to character classes defined by the XML specs. | https://github.com/lddubeau/xmlchars |
| npm | transitiva | yallist | 3.1.1 | Yet Another Linked List | https://github.com/isaacs/yallist |
| npm | transitiva | yocto-queue | 0.1.0 | Tiny queue data structure | sindresorhus/yocto-queue |
| npm | transitiva | yocto-spinner | 1.2.2 | Tiny terminal spinner | sindresorhus/yocto-spinner |
| npm | transitiva | yoctocolors | 2.2.0 | The smallest and fastest command-line coloring package on the internet | sindresorhus/yoctocolors |
| npm | transitiva | zod | 4.5.4 | TypeScript-first schema declaration and validation library with static type inference | https://github.com/colinhacks/zod |
| npm | transitiva | zod-to-json-schema | 3.25.2 | Converts Zod schemas to Json Schemas | https://github.com/StefanTerdell/zod-to-json-schema |
| npm | transitiva | zod-validation-error | 4.0.2 | Wrap zod validation errors in user-friendly readable messages | git://github.com/causaly/zod-validation-error |
<!-- specsfy:documentator:end -->
