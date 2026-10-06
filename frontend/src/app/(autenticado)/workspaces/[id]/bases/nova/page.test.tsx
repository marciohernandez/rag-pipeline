import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "workspace-1" }),
  useRouter: () => ({ push: vi.fn() }),
}));

import NovaBasePage from "@/app/(autenticado)/workspaces/[id]/bases/nova/page";
import { saveSession } from "@/lib/session";

const eu = (papel: "owner" | "member") => ({
  id: "p-1", nome: "Bia", email: "bia@exemplo.com", papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

beforeEach(() => sessionStorage.clear());
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("NovaBasePage", () => {
  it("mostra o fluxo em etapas para owner, com o retorno ao Workspace", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-owner", eu("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) =>
      String(url).includes("/auth/me") ? json(eu("owner")) : json({}, 500),
    );
    render(<NovaBasePage />);

    expect(await screen.findByRole("heading", { name: "Nova Base" })).toBeInTheDocument();
    expect(await screen.findByRole("navigation", { name: "Etapas" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voltar ao workspace/i })).toHaveAttribute("href", "/workspaces/workspace-1");
  });

  it("recusa member sem mostrar o fluxo", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-member", eu("member"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json(eu("member")));
    render(<NovaBasePage />);

    expect(await screen.findByText(/somente owner e admin podem criar bases/i)).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Etapas" })).not.toBeInTheDocument();
  });

  it("mostra falha com Tentar novamente quando a permissão não pode ser validada", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-owner", eu("owner"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "x" }, 500));
    render(<NovaBasePage />);

    expect(await screen.findByText(/não foi possível validar sua permissão/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
