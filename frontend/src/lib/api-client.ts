/**
 * Cliente HTTP único do frontend (SPEC-0013, US-001 / FR-001 / NFR-002).
 *
 * - injeta `Authorization: Bearer <token>` a partir da sessão;
 * - em 401 limpa a sessão e sinaliza que o app deve voltar ao Login
 *   (`ApiError.unauthorized`);
 * - nunca repassa detalhe de provedor: só o `detail` seguro do backend.
 */

import { avisarSessaoTerminada, clearSession, getToken } from "@/lib/session";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? ""
).replace(/\/+$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly unauthorized: boolean;
  readonly detail: string | null;

  constructor(status: number, detail: string | null) {
    super(detail ?? `Falha na requisição (${status}).`);
    this.name = "ApiError";
    this.status = status;
    this.unauthorized = status === 401;
    this.detail = detail;
  }
}

async function safeDetail(response: Response): Promise<string | null> {
  try {
    const corpo = (await response.clone().json()) as { detail?: unknown };
    return typeof corpo?.detail === "string" ? corpo.detail : null;
  } catch {
    return null;
  }
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = /^https?:\/\//.test(path) ? path : `${API_BASE_URL}${path}`;
  const response = await fetch(url, { ...init, headers });

  if (response.status === 401) {
    clearSession();
    if (token) avisarSessaoTerminada();
    throw new ApiError(401, await safeDetail(response));
  }
  if (!response.ok) {
    throw new ApiError(response.status, await safeDetail(response));
  }
  return response;
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  return (await response.json()) as T;
}
