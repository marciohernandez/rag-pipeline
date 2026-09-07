/**
 * Sessão de demonstração: guarda o token estático (SPEC-0013, US-001).
 *
 * O token vive apenas em `sessionStorage` — some ao fechar a aba e nunca é
 * enviado a outra origem. Todo acesso é protegido: em SSR ou modo privado
 * `sessionStorage` pode lançar, e nesse caso a sessão é tratada como vazia.
 */

const TOKEN_KEY = "rag.demo.token";

export function saveSession(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // sessionStorage indisponível — sem persistência nesta execução.
  }
}

export function getToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function clearSession(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // nada a limpar se o storage não está acessível.
  }
}

export function hasSession(): boolean {
  return getToken() !== null;
}

/**
 * Papel da demonstração derivado do token estático (`token-demo-<papel>`,
 * DEC-002). Enquanto não houver autenticação real nem endpoint de identidade,
 * é o que o cliente tem para decidir quais ações de escrita mostrar.
 * `token-demo-outro-tenant` é owner do tenant-2.
 */
export function getPapel(): "owner" | "admin" | "member" | null {
  const token = getToken();
  if (!token) return null;
  if (/member/.test(token)) return "member";
  if (/admin/.test(token)) return "admin";
  if (/owner|outro-tenant/.test(token)) return "owner";
  return null;
}
