/**
 * Apoio dos testes da SPEC-0020 (fase RED).
 *
 * Os componentes e módulos novos ainda não existem quando os testes são
 * escritos. Um `import` estático de um arquivo ausente derruba a coleta da
 * suíte, e isso não é um RED válido. `exigir` importa o módulo só no corpo do
 * teste e reprova por asserção quando ele ainda não existe; depois que o
 * módulo existir, o teste segue para as asserções de comportamento.
 */
import { expect } from "vitest";

export async function carregar<T>(caminho: string): Promise<T | null> {
  try {
    return (await import(/* @vite-ignore */ caminho)) as T;
  } catch {
    return null;
  }
}

export async function exigir<T>(caminho: string): Promise<T> {
  const modulo = await carregar<T>(caminho);
  expect(modulo, `${caminho} ainda não existe (comportamento da SPEC-0020 ausente)`).not.toBeNull();
  return modulo as T;
}
