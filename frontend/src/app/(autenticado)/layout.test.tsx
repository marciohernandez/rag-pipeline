import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
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
  saveSession("sessao-opaca-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LayoutAutenticado — breadcrumb", () => {
  it("marca Workspaces como página atual e mantém Equipe navegável", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respostaJson(pessoa("member")));
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    expect(trilha).toHaveTextContent("Equipe");
    expect(trilha).toHaveTextContent("Workspaces");
    expect(within(trilha).getByText("Workspaces")).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Equipe" })).toHaveAttribute("href", "/workspaces");
  });

  it("mostra nome real do Workspace e links acessíveis por teclado", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-017 AC-018
    navigation.pathname = "/workspaces/workspace-1";
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("member"))
        : respostaJson({ id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" }),
    );
    const user = userEvent.setup();
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    const atual = await within(trilha).findByText("Banda Larga PF — Vivo — Gold");
    expect(atual).toHaveAttribute("aria-current", "page");
    expect(within(trilha).getByRole("link", { name: "Workspaces" })).toHaveAttribute("href", "/workspaces");
    await user.tab();
    expect(screen.getByRole("link", { name: "Equipe" })).toHaveFocus();
    await user.tab();
    expect(within(trilha).getByRole("link", { name: "Workspaces" })).toHaveFocus();
  });

  it("mostra Equipe, Workspaces, Workspace e Base com página atual sem link", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-017 AC-018
    navigation.pathname = "/execucoes/base-1";
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("member"))
        : String(input).endsWith("/api/v1/bases/base-1")
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
      String(input).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("member"))
        : String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson({ id: "base-1", nome: nomeBase, workspace_id: "workspace-1" })
        : respostaJson({ id: "workspace-1", nome: nomeWorkspace }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const workspaceLink = await screen.findByRole("link", { name: nomeWorkspace });
    expect(workspaceLink.parentElement).toHaveClass("max-w-24", "truncate", "sm:max-w-none");
    expect(screen.getByText(nomeBase)).toHaveAttribute("aria-current", "page");
    expect(screen.getByText(nomeBase)).toHaveClass("[overflow-wrap:anywhere]");
  });

  it("mostra Equipe, Pessoas e o nome real da pessoa na trilha do detalhe", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-011 AC-014 AC-025
    navigation.pathname = "/pessoas/pessoa-2";
    const nome = `Beatriz ${"Albuquerque".repeat(8)}`;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("admin"))
        : respostaJson({ id: "pessoa-2", nome }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    expect(trilha).toHaveTextContent(/Equipe\s*\/\s*Pessoas/);
    expect(within(trilha).getByRole("link", { name: "Pessoas" })).toHaveAttribute(
      "href",
      "/pessoas",
    );
    expect(await within(trilha).findByText(nome)).toHaveAttribute("aria-current", "page");
    expect(within(trilha).getByText(nome)).toHaveClass("[overflow-wrap:anywhere]");
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

  it("não revela o conteúdo autenticado antes de validar a identidade", async () => {
    // SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023
    let concluir!: (resposta: Response) => void;
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise<Response>((resolve) => { concluir = resolve; }),
    );
    render(<LayoutAutenticado>Conteúdo reservado</LayoutAutenticado>);

    expect(screen.getByRole("status", { name: /carregando sessão/i })).toBeInTheDocument();
    expect(screen.queryByText("Conteúdo reservado")).not.toBeInTheDocument();

    concluir(respostaJson(pessoa("member")));
    expect(await screen.findByText("Conteúdo reservado")).toBeInTheDocument();
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
    expect(screen.queryByText("Conteúdo")).not.toBeInTheDocument();
  });

  it("mostra falha segura e permite tentar carregar a identidade novamente", async () => {
    // SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023
    const fetchSpy = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response('{"detail":"Falha interna."}', {
          status: 500,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(respostaJson(pessoa("member")));
    const user = userEvent.setup();
    render(<LayoutAutenticado>Conteúdo reservado</LayoutAutenticado>);

    expect(await screen.findByText(/não foi possível validar sua sessão/i)).toBeInTheDocument();
    expect(screen.queryByText("Conteúdo reservado")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));

    expect(await screen.findByText("Conteúdo reservado")).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(2);
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

describe("LayoutAutenticado — Conexões e Nova Base (SPEC-0026)", () => {
  beforeEach(() => {
    sessionStorage.clear();
    saveSession("sessao-opaca-spec-0026");
  });

  it("mostra o item Conexões somente a owner e admin", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me") ? respostaJson(pessoa("admin")) : respostaJson([]),
    );
    const { unmount } = render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);
    expect(await screen.findByRole("link", { name: "Conexões" })).toHaveAttribute("href", "/conexoes");
    unmount();

    spy.mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me") ? respostaJson(pessoa("member")) : respostaJson([]),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);
    expect(await screen.findByText("Conteúdo")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Conexões" })).not.toBeInTheDocument();
  });

  it("mostra Equipe, Conexões e o nome da conexão na trilha do detalhe", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    navigation.pathname = "/conexoes/con-1";
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("owner"))
        : respostaJson({ id: "con-1", nome: "OpenAI principal" }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    expect(trilha).toHaveTextContent(/Equipe\s*\/\s*Conexões/);
    expect(within(trilha).getByRole("link", { name: "Conexões" })).toHaveAttribute("href", "/conexoes");
    expect(await within(trilha).findByText("OpenAI principal")).toHaveAttribute("aria-current", "page");
  });

  it("mostra Equipe, Workspaces, Workspace e Nova Base na trilha da nova Base", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    navigation.pathname = "/workspaces/workspace-1/bases/nova";
    vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada) =>
      String(entrada).includes("/api/v1/auth/me")
        ? respostaJson(pessoa("owner"))
        : respostaJson({ id: "workspace-1", nome: "Banda Larga PF" }),
    );
    render(<LayoutAutenticado>Conteúdo</LayoutAutenticado>);

    const trilha = await screen.findByRole("navigation", { name: "Trilha" });
    expect(await within(trilha).findByRole("link", { name: "Banda Larga PF" })).toHaveAttribute(
      "href",
      "/workspaces/workspace-1",
    );
    expect(within(trilha).getByText("Nova Base")).toHaveAttribute("aria-current", "page");
  });
});
