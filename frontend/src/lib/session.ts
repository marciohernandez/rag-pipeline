/** Sessão autenticada mantida apenas durante a aba atual. */

const TOKEN_KEY = "rag.session.token";
const IDENTITY_KEY = "rag.session.identity";
const NOTICE_KEY = "rag.session.notice";

export interface PessoaSessao {
  id: string;
  nome: string;
  email: string;
  papel: "owner" | "admin" | "member";
  tenant_id: string;
  project_id: string;
  precisa_trocar_senha: boolean;
}

function pessoaSessaoValida(valor: unknown): valor is PessoaSessao {
  if (typeof valor !== "object" || valor === null) return false;
  const pessoa = valor as Record<string, unknown>;
  return (
    typeof pessoa.id === "string" &&
    typeof pessoa.nome === "string" &&
    typeof pessoa.email === "string" &&
    (pessoa.papel === "owner" ||
      pessoa.papel === "admin" ||
      pessoa.papel === "member") &&
    typeof pessoa.tenant_id === "string" &&
    typeof pessoa.project_id === "string" &&
    typeof pessoa.precisa_trocar_senha === "boolean"
  );
}

export function saveSession(token: string, pessoa?: PessoaSessao): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    if (pessoa) saveIdentity(pessoa);
  } catch {
    // Em SSR ou modo privado, a sessão é tratada como vazia.
  }
}

export function saveIdentity(pessoa: PessoaSessao): void {
  try {
    sessionStorage.setItem(IDENTITY_KEY, JSON.stringify(pessoa));
  } catch {
    // Cache dispensável; a identidade continua sendo validada pelo backend.
  }
}

export function getIdentity(): PessoaSessao | null {
  try {
    const valor = sessionStorage.getItem(IDENTITY_KEY);
    if (!valor) return null;
    const pessoa: unknown = JSON.parse(valor);
    return pessoaSessaoValida(pessoa) ? pessoa : null;
  } catch {
    return null;
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
    sessionStorage.removeItem(IDENTITY_KEY);
  } catch {
    // Nada a limpar quando o storage não está acessível.
  }
}

export function hasSession(): boolean {
  return getToken() !== null;
}

export function getPapel(): PessoaSessao["papel"] | null {
  return getIdentity()?.papel ?? null;
}

export function avisarSessaoTerminada(): void {
  try {
    sessionStorage.setItem(NOTICE_KEY, "Sua sessão terminou. Entre novamente.");
  } catch {
    // O aviso é complementar ao redirecionamento.
  }
}

export function consumirAviso(): string | null {
  try {
    const aviso = sessionStorage.getItem(NOTICE_KEY);
    sessionStorage.removeItem(NOTICE_KEY);
    return aviso;
  } catch {
    return null;
  }
}
