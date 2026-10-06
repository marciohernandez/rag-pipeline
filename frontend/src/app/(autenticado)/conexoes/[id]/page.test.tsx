import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "con-1" }),
  useRouter: () => ({ push: vi.fn() }),
}));

import ConexaoDetalhePage from "@/app/(autenticado)/conexoes/[id]/page";
import { saveSession } from "@/lib/session";

const eu = (papel: "owner" | "member") => ({
  id: "p-1", nome: "Bia", email: "bia@exemplo.com", papel,
  tenant_id: "tenant-1", project_id: "projeto-1", precisa_trocar_senha: false,
});
const conexao = {
  id: "con-1", nome: "Qdrant produção", tipo: "qdrant", situacao: "ativa",
  configuracao: { url: "https://qdrant.exemplo.com" }, segredo_definido: true,
  segredo_mascara: "••••••••", em_uso: 2, criado_em: "2026-10-06T12:00:00Z", atualizada_em: null,
};
const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

beforeEach(() => sessionStorage.clear());
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ConexaoDetalhePage", () => {
  it("mostra o detalhe com a chave mascarada e as ações", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-owner", eu("owner"));
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) =>
      String(url).includes("/auth/me") ? json(eu("owner")) : json(conexao),
    );
    render(<ConexaoDetalhePage />);

    expect(await screen.findByRole("heading", { name: "Qdrant produção" })).toBeInTheDocument();
    expect(screen.getByText("https://qdrant.exemplo.com")).toBeInTheDocument();
    expect(screen.getByText("••••••••")).toBeInTheDocument();
    for (const nome of [/^editar$/i, /^desativar$/i, /^excluir$/i]) {
      expect(screen.getByRole("button", { name: nome })).toBeInTheDocument();
    }
  });

  it("recusa member e diferencia a conexão não encontrada", async () => {
    // SPECSFY: SPEC-0026 US-001 US-004 FR-012 FR-014 NFR-002 NFR-004 AC-006 AC-018
    saveSession("sessao-opaca-member", eu("member"));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json(eu("member")));
    const { unmount } = render(<ConexaoDetalhePage />);
    expect(await screen.findByText(/não tem permissão para administrar conexões/i)).toBeInTheDocument();
    unmount();

    saveSession("sessao-opaca-owner", eu("owner"));
    vi.restoreAllMocks();
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url) =>
      String(url).includes("/auth/me") ? json(eu("owner")) : json({ detail: "x" }, 404),
    );
    render(<ConexaoDetalhePage />);
    expect(await screen.findByText(/não existe ou não pertence à sua equipe/i)).toBeInTheDocument();
  });
});
