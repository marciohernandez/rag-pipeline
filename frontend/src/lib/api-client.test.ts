import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Módulos ainda não existem (RED de T010).
import { apiFetch } from "@/lib/api-client";
import { getToken, saveSession } from "@/lib/session";

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("apiFetch", () => {
  it("injeta o Authorization: Bearer a partir da sessão", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-003 (SPEC-0013)
    saveSession("token-demo-owner");
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("[]", { status: 200 }));

    await apiFetch("/api/v1/bases");

    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer token-demo-owner");
  });

  it("em 401 limpa a sessão e sinaliza redirecionamento ao Login", async () => {
    // SPECSFY: US-001 FR-001 NFR-002 AC-003 (SPEC-0013)
    saveSession("token-demo-owner");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"nope"}', { status: 401 }),
    );

    await expect(apiFetch("/api/v1/bases")).rejects.toMatchObject({
      status: 401,
      unauthorized: true,
    });
    expect(getToken()).toBeNull();
  });
});
