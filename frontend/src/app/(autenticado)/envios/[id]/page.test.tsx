import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({ useParams: () => ({ id: "env-3" }) }));

import EnvioDetalhePage from "@/app/(autenticado)/envios/[id]/page";
import { enviosExemplo, json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca", {
    id: "p1", nome: "Pessoa de teste", email: "owner@exemplo.com", papel: "owner",
    tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Detalhe do envio", () => {
  it("mostra o envio que falhou, o link para a coleção e a ação Repetir", async () => {
    // SPECSFY: SPEC-0030 US-002 US-003 FR-012 AC-007 AC-009
    simularFetch({
      "GET .*/api/v1/envios/env-3$": () =>
        json({ ...enviosExemplo[2], colecao: { id: "colecao-1", nome: "manuais", workspace_id: "workspace-1" } }),
    });
    render(<EnvioDetalhePage />);

    expect(await screen.findByRole("button", { name: "Repetir" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Falha ao processar o envio");
    expect(screen.getByRole("link", { name: "Ver coleção" })).toHaveAttribute(
      "href", "/workspaces/workspace-1/colecoes/colecao-1",
    );
  });

  it("diferencia envio inexistente de falha de rede", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-012 NFR-001 AC-019
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "x" }, 404));
    render(<EnvioDetalhePage />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Envio não encontrado.");
    expect(screen.queryByRole("button", { name: /tentar novamente/i })).toBeNull();
  });
});
