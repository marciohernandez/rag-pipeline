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
const colecoes = [
  { id: "colecao-1", nome: "manuais", documentos: 2, chunks: 8, ultimo_envio_em: "2026-09-18T10:00:00Z" },
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
    if (url.includes("/api/v1/workspaces/workspace-1/colecoes")) {
      return respostaJson(colecoes);
    }
    if (url.includes("/api/v1/conversoes?workspace_id=workspace-1")) {
      return respostaJson([]);
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
  it("mostra a estrutura de loading enquanto lê Workspace e coleções", () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));

    render(<WorkspaceDetalhePage />);

    expect(screen.getByText(/carregando coleções/i)).toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveAttribute("aria-busy", "true");
  });

  it("lista as coleções do Workspace e abre as ações de escrita para owner", async () => {
    // SPECSFY: SPEC-0019 US-002 FR-003 FR-004 FR-008 AC-005 AC-006 AC-007
    saveSession("sessao-opaca-owner", identidade("owner"));
    const fetchSpy = mockDetalhe();
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
    expect(screen.getByText("colecao-1")).toBeInTheDocument();
    expect(
      fetchSpy.mock.calls.some(([url]) =>
        String(url).includes("/api/v1/workspaces/workspace-1/colecoes"),
      ),
    ).toBe(true);

    expect(screen.getByRole("link", { name: /enviar documentos/i })).toHaveAttribute(
      "href",
      "/workspaces/workspace-1/enviar",
    );

    await user.click(screen.getByRole("button", { name: /editar nome/i }));
    expect(await screen.findByRole("dialog", { name: /editar workspace/i })).toBeInTheDocument();
    await user.keyboard("{Escape}");

    await user.click(screen.getByRole("button", { name: /^apagar workspace$/i }));
    expect(await screen.findByRole("dialog", { name: /apagar workspace/i })).toHaveTextContent(
      /apague as coleções/i,
    );
  });

  it("mantém member em modo somente leitura", async () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-003 AC-017 AC-018
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText("colecao-1")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /enviar documentos/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /editar nome/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apagar workspace/i })).not.toBeInTheDocument();
  });

  it("orienta quando o Workspace ainda não possui coleções", async () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/colecoes")) return respostaJson([]);
      if (url.includes("/api/v1/conversoes?")) return respostaJson([]);
      return respostaJson(workspace);
    });
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText(/nenhuma coleção ainda/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /enviar documentos/i })).toBeInTheDocument();
    expect(screen.queryByText(/nova base/i)).toBeNull();
  });

  it("abre a coleção por teclado", async () => {
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    const linha = await screen.findByRole("row", { name: /coleção manuais/i });
    linha.focus();
    await user.keyboard("{Enter}");

    expect(push).toHaveBeenCalledWith("/workspaces/workspace-1/colecoes/colecao-1");
  });

  it("diferencia 404 de erro genérico e permite recuperar falha transitória", async () => {
    saveSession("sessao-opaca-owner", identidade("owner"));
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(respostaJson({ detail: "ausente" }, 500))
      .mockResolvedValueOnce(respostaJson(colecoes))
      .mockResolvedValueOnce(respostaJson([]))
      .mockResolvedValueOnce(respostaJson(workspace))
      .mockResolvedValueOnce(respostaJson(colecoes))
      .mockResolvedValueOnce(respostaJson([]))
      // SPEC-0037: a seção "Domínio da empresa" lê domínio, versões, IA e conexões.
      .mockResolvedValueOnce(respostaJson({ versao: null, texto: "" }))
      .mockResolvedValueOnce(respostaJson([]))
      .mockResolvedValueOnce(respostaJson({ ia_externa_permitida: false, conexao_ia_id: null }))
      .mockResolvedValueOnce(respostaJson([]));
    const user = userEvent.setup();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/não foi possível carregar/i);
    await user.click(screen.getByRole("button", { name: /tentar novamente/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(10));
    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
  });

  it("leva owner à página Enviar documentos e não abre mais o painel de envio", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-owner", identidade("owner"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByRole("heading", { name: workspace.nome })).toBeInTheDocument();
    const acao = screen.getByRole("link", { name: /enviar documentos/i });
    expect(acao).toHaveAttribute("href", "/workspaces/workspace-1/enviar");
    expect(screen.queryByRole("button", { name: /enviar base/i })).not.toBeInTheDocument();
  });

  it("não mostra a ação de enviar documentos para member", async () => {
    // SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016
    saveSession("sessao-opaca-member", identidade("member"));
    mockDetalhe();
    render(<WorkspaceDetalhePage />);

    expect(await screen.findByText("colecao-1")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /enviar documentos/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /enviar documentos/i })).not.toBeInTheDocument();
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
