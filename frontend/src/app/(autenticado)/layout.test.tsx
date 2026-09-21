import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const navigation = vi.hoisted(() => ({ pathname: "/workspaces", replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useRouter: () => ({ replace: navigation.replace }),
}));

import LayoutAutenticado from "@/app/(autenticado)/layout";
import { saveSession } from "@/lib/session";

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
