import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

import ConexoesPage from "@/app/(autenticado)/conexoes/page";
import { saveSession } from "@/lib/session";

const eu = (papel: "owner" | "admin" | "member") => ({
  id: "p-1", nome: "Bia", email: "bia@exemplo.com", papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});
const conexao = {
  id: "con-1", nome: "OpenAI principal", tipo: "embeddings_openai", situacao: "ativa",
  configuracao: { modelo: "m", dimensoes: 8 }, segredo_definido: true,
  segredo_mascara: "••••••••", em_uso: 0,
};
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

beforeEach(() => sessionStorage.clear());
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ConexoesPage", () => {
  it("lista as conexões e oferece Nova conexão para owner", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-owner", eu("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) =>
      String(url).includes("/auth/me") ? json(eu("owner")) : json([conexao]),
    );
    render(<ConexoesPage />);

    expect(await screen.findByText("OpenAI principal")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Conexões" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /nova conexão/i })).toBeInTheDocument();
    expect(screen.queryByText(/sk-/)).not.toBeInTheDocument();
  });

  it("recusa member sem chamar a API de conexões", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-member", eu("member"));
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(eu("member")));
    render(<ConexoesPage />);

    expect(await screen.findByText(/não tem permissão para administrar conexões/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /nova conexão/i })).not.toBeInTheDocument();
    expect(spy.mock.calls.some(([url]) => String(url).endsWith("/api/v1/conexoes"))).toBe(false);
  });

  it("desativa pela ação da linha e anuncia o resultado", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-admin", eu("admin"));
    const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async (url) => {
      const alvo = String(url);
      if (alvo.includes("/auth/me")) return json(eu("admin"));
      if (alvo.endsWith("/desativar")) return json({ ...conexao, situacao: "desativada" });
      return json([conexao]);
    });
    const user = userEvent.setup();
    render(<ConexoesPage />);

    await user.click(await screen.findByRole("button", { name: /desativar openai principal/i }));

    await waitFor(() =>
      expect(spy.mock.calls.some(([url]) => String(url).endsWith("/api/v1/conexoes/con-1/desativar"))).toBe(true),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(/desativada/i);
  });

  it("mostra erro com Tentar novamente quando a lista falha", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-owner", eu("owner"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "falha" }, 500));
    render(<ConexoesPage />);

    expect(await screen.findByText(/não foi possível carregar as conexões/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
