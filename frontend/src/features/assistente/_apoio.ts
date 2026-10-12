/**
 * Apoio dos testes da SPEC-0021 (fase RED): resposta HTTP simulada do backend
 * do assistente, sem tocar a rede. Vive ao lado dos testes porque só eles a usam.
 */
import { vi } from "vitest";

export const conversaAntiga = {
  id: "c-antiga",
  titulo: "Conversa antiga",
  atualizada_em: "2026-09-20T10:00:00Z",
};

export function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function pessoa(papel = "member") {
  return {
    id: "pessoa-1",
    nome: "Bia Costa",
    email: "bia@exemplo.com",
    papel,
    tenant_id: "tenant-1",
    project_id: "projeto-1",
    precisa_trocar_senha: false,
  };
}

export function mensagem(
  papel: "pessoa" | "assistente",
  conteudo: string,
  extra: Record<string, unknown> = {},
) {
  return {
    id: `m-${Math.random().toString(36).slice(2)}`,
    papel,
    conteudo,
    fontes: [],
    colecao_id: null,
    criada_em: "2026-09-20T10:00:00Z",
    ...extra,
  };
}

/** Simula os endpoints do assistente e de apoio; devolve o spy de `fetch`. */
export function simularApi(
  detalhes: Record<string, unknown> = {},
  sobrescrever?: (url: string, init: RequestInit) => Response | undefined,
) {
  const historico = [conversaAntiga];
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada, init = {}) => {
    const url = String(entrada);
    const metodo = (init.method ?? "GET").toUpperCase();
    const proprio = sobrescrever?.(url, init);
    if (proprio) return proprio;
    if (url.includes("/auth/me")) return json(pessoa());
    if (url.includes("/api/v1/colecoes")) return json([]);
    if (url.endsWith("/assistente/conversas") && metodo === "GET") return json(historico);
    if (url.endsWith("/assistente/conversas") && metodo === "POST") {
      const nova = { id: "c-nova", titulo: "Nova conversa" };
      return json(nova, 201);
    }
    if (url.endsWith("/mensagens") && metodo === "POST") {
      historico.unshift({
        id: "c-nova",
        titulo: "Qual splitter usar",
        atualizada_em: "2026-09-24T10:00:00Z",
      });
      return json(
        {
          mensagem_pessoa: mensagem("pessoa", "Qual splitter usar?"),
          mensagem_assistente: mensagem("assistente", "Resposta nova do assistente", {
            fontes: ["docs/architecture.md"],
          }),
        },
        201,
      );
    }
    const id = url.split("/assistente/conversas/")[1];
    if (id && metodo === "GET" && id in detalhes) return json(detalhes[id]);
    return json({});
  });
}
