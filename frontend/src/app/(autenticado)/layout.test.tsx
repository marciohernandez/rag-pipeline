import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigation = vi.hoisted(() => ({ pathname: "/workspaces", replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useRouter: () => ({ replace: navigation.replace }),
}));

import LayoutAutenticado from "@/app/(autenticado)/layout";
import { getToken, saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

function respostaJson(payload: unknown) {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  navigation.pathname = "/workspaces";
  navigation.replace.mockReset();
  sessionStorage.clear();
  saveSession("token-demo-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LayoutAutenticado — breadcrumb", () => {
  it("marca Workspaces como página atual e mantém Equipe navegável", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    expect(trilha).toHaveTextContent("Equipe");
    expect(trilha).toHaveTextContent("Workspaces");
    expect(screen.getByText("Workspaces")).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Equipe" })).toHaveAttribute("href", "/workspaces");
  });

  it("mostra nome real do Workspace e links acessíveis por teclado", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-017 AC-018
    navigation.pathname = "/workspaces/workspace-1";
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respostaJson({ id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" }),
    );
    const user = userEvent.setup();
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const atual = await screen.findByText("Banda Larga PF — Vivo — Gold");
    expect(atual).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Workspaces" })).toHaveAttribute("href", "/workspaces");
    await user.tab();
    expect(screen.getByRole("link", { name: "Equipe" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("link", { name: "Workspaces" })).toHaveFocus();
  });

  it("mostra Equipe, Workspaces, Workspace e Base com página atual sem link", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-017 AC-018
    navigation.pathname = "/execucoes/base-1";
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson({ id: "base-1", nome: "Catálogo", workspace_id: "workspace-1" })
        : respostaJson({ id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const atual = await screen.findByText("Catálogo");
    expect(atual).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Banda Larga PF — Vivo — Gold" })).toHaveAttribute(
      "href", "/workspaces/workspace-1",
    );
    expect(screen.getByRole("navigation", { name: "Trilha" })).toHaveTextContent(
      /Equipe\s*\/\s*Workspaces\s*\/\s*Banda Larga PF — Vivo — Gold\s*\/\s*Catálogo/,
    );
  });

  it("preserva nomes longos acessíveis mesmo quando o Workspace intermediário trunca no mobile", async () => {
    navigation.pathname = "/execucoes/base-1";
    const nomeWorkspace = `Workspace ${"atendimento".repeat(15)}`;
    const nomeBase = `Base ${"ofertas".repeat(15)}`;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson({ id: "base-1", nome: nomeBase, workspace_id: "workspace-1" })
        : respostaJson({ id: "workspace-1", nome: nomeWorkspace }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const workspaceLink = await screen.findByRole("link", { name: nomeWorkspace });
    expect(workspaceLink.parentElement).toHaveClass("max-w-24", "truncate", "sm:max-w-none");
    expect(screen.getByText(nomeBase)).toHaveAttribute("aria-current", "page");
    expect(screen.getByText(nomeBase)).toHaveClass("[overflow-wrap:anywhere]");
  });
});

// --------------------------------------------------------------------------
// SPEC-0020 — identidade vinda do backend e navegação persistente (fase RED).
// --------------------------------------------------------------------------

function pessoa(papel: string, precisaTrocarSenha = false) {
  return {
    id: "pessoa-1",
    nome: "Bia Costa",
    email: "bia@exemplo.com",
    papel,
    tenant_id: "tenant-1",
    project_id: "projeto-1",
    precisa_trocar_senha: precisaTrocarSenha,
  };
}

describe("LayoutAutenticado — identidade da pessoa (SPEC-0020)", () => {
  beforeEach(() => {
    sessionStorage.clear();
    saveSession("sessao-opaca-com-admin-no-texto");
  });

  it("obtém nome e papel do backend, sem deduzir o papel do texto do token", async () => {
    // SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (entrada) =>
        String(entrada).includes("/api/v1/auth/me") ? respostaJson(pessoa("member")) : respostaJson([]),
      );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    expect(await screen.findByRole("button", { name: /bia costa/i })).toBeInTheDocument();
    expect(fetchSpy.mock.calls.some(([u]) => String(u).includes("/api/v1/auth/me"))).toBe(true);
    expect(screen.queryByRole("link", { name: "Pessoas" })).not.toBeInTheDocument();
  });

  it("mostra os itens Workspaces e Pessoas na navegação para owner e admin", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-024
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me") ? respostaJson(pessoa("admin")) : respostaJson([]),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const pessoas = await screen.findByRole("link", { name: "Pessoas" });
    expect(pessoas).toHaveAttribute("href", "/pessoas");
    expect(screen.getAllByRole("link", { name: "Workspaces" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Equipe" })).toBeInTheDocument();
  });

  it("leva a Nova senha quando a senha ainda está pendente", async () => {
    // SPECSFY: SPEC-0020 US-001 US-002 FR-004 FR-014 AC-006 AC-023
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me") ? respostaJson(pessoa("member", true)) : respostaJson([]),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/nova-senha"));
  });

  it("volta ao Login com aviso e sessão limpa quando o backend responde 401", async () => {
    // SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-009 AC-023
    const sessao = await exigir<{ consumirAviso: () => string | null }>("@/lib/session");
    expect(typeof sessao.consumirAviso).toBe("function");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Sessão inválida."}', {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/login"));
    expect(getToken()).toBeNull();
    expect(sessao.consumirAviso()).toBe("Sua sessão terminou. Entre novamente.");
  });
});
