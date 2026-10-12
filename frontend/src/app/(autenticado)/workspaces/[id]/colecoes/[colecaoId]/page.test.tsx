import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "workspace-1", colecaoId: "colecao-1" }),
  useRouter: () => ({ push }),
  useSearchParams: () => new URLSearchParams(),
}));

import ColecaoDetalhePage from "@/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/page";
import { documentosExemplo, enviosExemplo, json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";

const identidade = (papel: "owner" | "member") => ({
  id: `pessoa-${papel}`, nome: "Pessoa de teste", email: `${papel}@exemplo.com`, papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});

const colecao = {
  id: "colecao-1", nome: "manuais", workspace_id: "workspace-1", workspace_nome: "Clientes", dimensao: 1536,
  conexao_embeddings: { id: "e", nome: "OpenAI principal" }, conexao_vector_store: { id: "q", nome: "Qdrant produção" },
  documentos: 2, chunks: 17, criado_em: "2026-10-09T09:00:00Z", criado_por: null,
};

function simular() {
  return simularFetch({
    "GET .*/api/v1/colecoes/colecao-1$": () => json(colecao),
    "GET .*/api/v1/colecoes/colecao-1/documentos$": () => json(documentosExemplo),
    "GET .*/api/v1/colecoes/colecao-1/envios$": () => json(enviosExemplo.slice(0, 2)),
  });
}

beforeEach(() => {
  sessionStorage.clear();
  push.mockReset();
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Detalhe da coleção", () => {
  it("abre em Documentos, mostra as ações de owner e troca para a aba Envios", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-008 FR-012 FR-015 AC-008 AC-009
    saveSession("sessao-opaca", identidade("owner"));
    simular();
    const user = userEvent.setup();
    render(<ColecaoDetalhePage />);

    expect(await screen.findByRole("heading", { name: "manuais" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Documentos", selected: true })).toBeInTheDocument();
    expect(await screen.findByRole("row", { name: /documento a\.md/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Adicionar documentos" })).toHaveAttribute(
      "href", "/workspaces/workspace-1/enviar?colecao=colecao-1",
    );
    expect(screen.getByRole("button", { name: "Renomear" })).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Envios" }));
    expect(await screen.findByRole("row", { name: /envio env-2/i })).toBeInTheDocument();
  });

  it("mantém member só com leitura e consulta", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-008 FR-015 AC-008 AC-012
    saveSession("sessao-opaca", identidade("member"));
    simular();
    render(<ColecaoDetalhePage />);

    expect(await screen.findByRole("heading", { name: "manuais" })).toBeInTheDocument();
    expect(await screen.findByRole("row", { name: /documento b\.md/i })).toBeInTheDocument();
    for (const nome of ["Adicionar documentos", "Renomear", "Apagar", "Substituir"]) {
      expect(screen.queryByRole("link", { name: nome })).toBeNull();
      expect(screen.queryByRole("button", { name: nome })).toBeNull();
    }
    expect(screen.getByRole("tab", { name: "Consulta" })).toBeInTheDocument();
  });

  it("diferencia coleção inexistente de erro transitório", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-008 NFR-001 AC-019
    saveSession("sessao-opaca", identidade("owner"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ detail: "segredo" }, 404));
    render(<ColecaoDetalhePage />);

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Coleção não encontrada.");
    expect(alerta).not.toHaveTextContent(/segredo/);
    expect(screen.queryByRole("button", { name: /tentar novamente/i })).toBeNull();
  });

  it("não tem violações de acessibilidade nas abas Documentos e Envios", async () => {
    // SPECSFY: SPEC-0030 NFR-003 FR-008 AC-021
    saveSession("sessao-opaca", identidade("owner"));
    simular();
    const user = userEvent.setup();
    const { container } = render(<ColecaoDetalhePage />);
    await screen.findByRole("row", { name: /documento a\.md/i });
    const axe = (await import("axe-core")).default;
    const regras = { rules: { "color-contrast": { enabled: false }, region: { enabled: false } } };

    expect((await axe.run(container, regras)).violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
    await user.click(screen.getByRole("tab", { name: "Envios" }));
    await screen.findByRole("row", { name: /envio env-2/i });
    expect((await axe.run(container, regras)).violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
  });
});
