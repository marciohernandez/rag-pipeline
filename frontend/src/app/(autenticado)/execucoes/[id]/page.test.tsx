import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "base-1" }),
  useRouter: () => ({ push }),
}));

import ExecucaoDetalhePage from "@/app/(autenticado)/execucoes/[id]/page";
import { saveSession } from "@/lib/session";

const base = {
  id: "base-1",
  nome: "Catálogo de ofertas",
  origem: "upload",
  documentos: 2,
  criado_em: "2026-09-19T10:00:00Z",
  workspace_id: "workspace-1",
  collection_name: "ofertas_gold",
  execucoes: [],
};
const workspace = { id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" };

function respostaJson(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  push.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-member");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ExecucaoDetalhePage", () => {
  it("mantém o loading enquanto lê o contexto da Base", () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));

    render(<ExecucaoDetalhePage />);

    expect(screen.getByText(/carregando/i)).toBeInTheDocument();
    expect(screen.queryByText(/ofertas_gold/i)).not.toBeInTheDocument();
  });

  it("exibe nome do Workspace e coleção persistida no PageHeader", async () => {
    // SPECSFY: SPEC-0019 US-002 FR-005 FR-006 NFR-003 AC-011 AC-012 AC-013
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/v1/bases/base-1")) return respostaJson(base);
      if (url.endsWith("/api/v1/workspaces/workspace-1")) return respostaJson(workspace);
      throw new Error(`URL inesperada: ${url}`);
    });

    render(<ExecucaoDetalhePage />);

    expect(await screen.findByRole("heading", { name: "Base Catálogo de ofertas" })).toBeInTheDocument();
    expect(screen.getByText(/Workspace: Banda Larga PF — Vivo — Gold/)).toHaveTextContent(
      /Coleção: ofertas_gold/,
    );
    expect(fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/api/v1/workspaces/workspace-1"))).toBe(true);
    expect(screen.getByText(/ainda não tem execuções/i)).toBeInTheDocument();
  });

  it("oferece retorno ao Workspace navegável por teclado", async () => {
    // SPECSFY: SPEC-0019 US-002 FR-005 AC-011
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson(base)
        : respostaJson(workspace),
    );
    const user = userEvent.setup();
    render(<ExecucaoDetalhePage />);

    const voltar = await screen.findByRole("link", { name: "Voltar ao Workspace" });
    expect(voltar).toHaveAttribute("href", "/workspaces/workspace-1");
    await user.tab();
    expect(voltar).toHaveFocus();
  });

  it("mantém nomes longos completos e com quebra no cabeçalho", async () => {
    const nomeLongo = `Workspace ${"atendimento".repeat(15)}`;
    const colecaoLonga = `colecao_${"longa".repeat(20)}`;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson({ ...base, collection_name: colecaoLonga })
        : respostaJson({ ...workspace, nome: nomeLongo }),
    );
    render(<ExecucaoDetalhePage />);

    const contexto = await screen.findByText(new RegExp(colecaoLonga));
    expect(contexto).toHaveTextContent(nomeLongo);
    expect(contexto).toHaveClass("[overflow-wrap:anywhere]");
  });

  it("mostra 404 seguro sem solicitar Workspace de Base ausente", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respostaJson({ detail: "tenant secreto" }, 404),
    );
    render(<ExecucaoDetalhePage />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Base não encontrada.");
    expect(alerta).not.toHaveTextContent(/tenant secreto/i);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("não confunde falha de leitura do Workspace com Base ausente", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      String(input).endsWith("/api/v1/bases/base-1")
        ? respostaJson(base)
        : respostaJson({ detail: "tenant secreto" }, 404),
    );
    render(<ExecucaoDetalhePage />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Não foi possível carregar o contexto do Workspace.");
    expect(alerta).not.toHaveTextContent(/tenant secreto|base não encontrada/i);
  });
});
