import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { json, simularFetch } from "./_apoio";

interface Props {
  open: boolean;
  colecao: { id: string; nome: string; documentos: number; chunks: number };
  onDeleted: (id: string) => void;
}
type Modulo = { default: ComponentType<Props> };
const colecao = { id: "c1", nome: "manuais", documentos: 2, chunks: 17 };

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

describe("ApagarColecaoDialog", () => {
  it("habilita Apagar coleção só com o nome exato digitado", async () => {
    // SPECSFY: SPEC-0030 US-005 FR-011 FR-015 AC-014
    const { default: ApagarColecaoDialog } = await exigir<Modulo>("@/features/colecoes/ApagarColecaoDialog");
    const chamadas = simularFetch({ "DELETE .*/api/v1/colecoes/c1$": () => new Response(null, { status: 204 }) });
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(<ApagarColecaoDialog open colecao={colecao} onDeleted={onDeleted} />);

    const dialogo = screen.getByRole("dialog");
    expect(dialogo).toHaveTextContent("manuais");
    expect(dialogo).toHaveTextContent(/2 documentos/);
    expect(dialogo).toHaveTextContent(/17 chunks/);
    const apagar = screen.getByRole("button", { name: /apagar/i });
    expect(apagar).toBeDisabled();

    const campo = screen.getByLabelText(/digite o nome da coleção para confirmar/i);
    await user.type(campo, "manua");
    expect(apagar).toBeDisabled();
    await user.type(campo, "is");
    expect(apagar).toBeEnabled();

    await user.click(apagar);

    const [, init] = chamadas.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("DELETE");
    expect(JSON.parse(String(init.body))).toEqual({ confirmacao_nome: "manuais" });
    expect(onDeleted).toHaveBeenCalledWith("c1");
  });

  it("mostra o erro seguro e mantém o diálogo quando a exclusão falha", async () => {
    // SPECSFY: SPEC-0030 US-005 FR-011 NFR-004 NFR-001 AC-015
    const { default: ApagarColecaoDialog } = await exigir<Modulo>("@/features/colecoes/ApagarColecaoDialog");
    simularFetch({
      "DELETE .*/api/v1/colecoes/c1$": () =>
        json({ detail: "Não foi possível apagar a coleção. Tente novamente." }, 502),
    });
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(<ApagarColecaoDialog open colecao={colecao} onDeleted={onDeleted} />);

    await user.type(screen.getByLabelText(/digite o nome da coleção para confirmar/i), "manuais");
    await user.click(screen.getByRole("button", { name: /apagar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível apagar a coleção. Tente novamente.",
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /apagar/i })).toBeEnabled();
    expect(onDeleted).not.toHaveBeenCalled();
  });
});
