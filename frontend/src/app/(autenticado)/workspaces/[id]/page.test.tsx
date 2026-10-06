import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "workspace-1" }),
  useRouter: () => ({ push }),
}));

import WorkspaceDetalhePage from "@/app/(autenticado)/workspaces/[id]/page";
import { saveSession } from "@/lib/session";

const identidade = (papel: "owner" | "member") => ({
  id: `pessoa-${papel}`, nome: "Pessoa de teste", email: `${papel}@exemplo.com`, papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});

const workspace = { id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" };
const bases = [
  {
    id: "base-1",
    origem: "upload",
    status: "succeeded",
    documentos: 2,
    chunks: 8,
    ultima_atualizacao: "2026-09-18T10:00:00Z",
  },
];

function respostaJson(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function mockDetalhe() {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/v1/workspaces/workspace-1")) {
      return respostaJson(workspace);
    }
    if (url.includes("/api/v1/bases?workspace_id=workspace-1")) {
      return respostaJson(bases);
    }
    throw new Error(`URL inesperada: ${url}`);
  });
}

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("WorkspaceDetalhePage", () => {
  it("mostra a estrutura de loading enquanto lê Workspace e Bases", () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));

    render(<WorkspaceDetalhePage />);

    expect(screen.getByText(/carregando bases/i)).toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveAttribute("aria-busy", "true");
  });

  it("filtra Bases pelo Workspace e abre as ações de escrita para owner", async () => {
    // SPECSFY: SPEC-0019 US-002 FR-003 FR-004 FR-008 AC-005 AC-006 AC-007
    saveSession("sessao-opaca-owner", identidade("owner"));
    const fetchSpy = mockDetalhe();
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
    expect(screen.getByText("base-1")).toBeInTheDocument();
    expect(
      fetchSpy.mock.calls.some(([url]) =>
        String(url).includes("/api/v1/bases?workspace_id=workspace-1"),
      ),
    ).toBe(true);

    expect(screen.getByRole("link", { name: /nova base/i })).toHaveAttribute(
      "href",
      "/workspaces/workspace-1/bases/nova",
    );

    await user.click(screen.getByRole("button", { name: /editar nome/i }));
    expect(await screen.findByRole("dialog", { name: /editar workspace/i })).toBeInTheDocument();
    await user.keyboard("{Escape}");

    await user.click(screen.getByRole("button", { name: /^apagar workspace$/i }));
    expect(await screen.findByRole("dialog", { name: /apagar workspace/i })).toHaveTextContent(
      /apague ou mova as bases/i,
    );
  });

  it("mantém member em modo somente leitura", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017 AC-018
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText("base-1")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /nova base/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /editar nome/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apagar workspace/i })).not.toBeInTheDocument();
  });

  it("orienta quando o Workspace ainda não possui Bases", async () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).includes("/api/v1/bases?")
        ? respostaJson([])
        : respostaJson(workspace),
    );
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText(/nenhuma base ainda/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /nova base/i })).toBeInTheDocument();
  });

  it("preserva a navegação da Base por teclado", async () => {
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    const linha = await screen.findByRole("row", { name: /base base-1/i });
    linha.focus();
    await user.keyboard("{Enter}");

    expect(push).toHaveBeenCalledWith("/execucoes/base-1");
  });

  it("diferencia 404 de erro genérico e permite recuperar falha transitória", async () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(respostaJson({ detail: "ausente" }, 500))
      .mockResolvedValueOnce(respostaJson(bases))
      .mockResolvedValueOnce(respostaJson(workspace))
      .mockResolvedValueOnce(respostaJson(bases));
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível carregar/i);
    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(4));
    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
  });

  it("leva owner à página de nova Base e não abre mais o painel de envio", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-owner", identidade("owner"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
    const acao = screen.getByRole("link", { name: /nova base/i });
    expect(acao).toHaveAttribute("href", "/workspaces/workspace-1/bases/nova");
    expect(screen.queryByRole("button", { name: /enviar base/i })).not.toBeInTheDocument();
  });

  it("não mostra a ação de nova Base para member", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText("base-1")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /nova base/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /nova base/i })).not.toBeInTheDocument();
  });

  it("mostra estado não encontrado sem expor detalhe do backend", async () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respostaJson({ detail: "tenant secreto" }, 404),
    );
    render(<WorkspaceDetalhePage />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Workspace não encontrado.");
    expect(alerta).not.toHaveTextContent(/tenant secreto/i);
    expect(screen.queryByRole("button", { name: /tentar novamente/i })).not.toBeInTheDocument();
  });
});
