import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Módulos ainda não existem (RED de T010).
import { apiFetch } from "@/lib/api-client";
import {
  consumirAviso,
  getIdentity,
  getPapel,
  getToken,
  saveSession,
} from "@/lib/session";

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("apiFetch", () => {
  it("mantém token e identidade somente na sessão da aba", () => {
    const pessoa = {
      id: "pessoa-1",
      nome: "Ana",
      email: "ana@example.com",
      papel: "owner" as const,
      tenant_id: "tenant-1",
      project_id: "projeto-1",
      precisa_trocar_senha: false,
    };

    saveSession("sessao-opaca-owner", pessoa);

    expect(getToken()).toBe("sessao-opaca-owner");
    expect(getIdentity()).toEqual(pessoa);
    expect(getPapel()).toBe("owner");
    expect(localStorage.length).toBe(0);
  });

  it("injeta o Authorization: Bearer a partir da sessão", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-003 (SPEC-0013)
    saveSession("sessao-opaca-owner");
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("[]", { status: 200 }));

    await apiFetch("/api/v1/bases");

    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer sessao-opaca-owner");
  });

  it("em 401 limpa a sessão e sinaliza redirecionamento ao Login", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-003 (SPEC-0013)
    saveSession("sessao-opaca-owner");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"nope"}', { status: 401 }),
    );

    await expect(apiFetch("/api/v1/bases")).rejects.toMatchObject({
      status: 401,
      unauthorized: true,
    });
    expect(getToken()).toBeNull();
    expect(consumirAviso()).toBe("Sua sessão terminou. Entre novamente.");
  });
});
