import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { json, simularFetch } from "@/features/colecoes/_apoio";
import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Props {
  open: boolean;
  onOpenChange?: (aberto: boolean) => void;
  colecaoId: string;
  abertas: number;
  onLiberada?: () => void;
}
type Modulo = { default: ComponentType<Props> };

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

const posts = (chamadas: ReturnType<typeof simularFetch>) =>
  chamadas.mock.calls.filter(([, init]) => init?.method === "POST");

describe("LiberarColecaoDialog", () => {
  it("informa a contagem de abertas e só libera após a confirmação explícita", async () => {
    // SPECSFY: SPEC-0039 US-005 FR-007 NFR-004 AC-020
    const { default: Dialogo } = await exigir<Modulo>("@/features/decisoes/LiberarColecaoDialog");
    const chamadas = simularFetch({
      "POST .*/api/v1/colecoes/c1/revisar$": () => json({ abertas: 3 }),
    });
    const onLiberada = vi.fn();
    const user = userEvent.setup();
    render(<Dialogo open colecaoId="c1" abertas={3} onLiberada={onLiberada} />);

    expect(screen.getByRole("dialog")).toHaveTextContent(/3 contradições abertas/i);
    expect(posts(chamadas)).toHaveLength(0);

    await user.click(screen.getByRole("button", { name: /liberar mesmo assim/i }));

    expect(JSON.parse(String(posts(chamadas)[0][1]?.body))).toEqual({ confirmado: true });
    expect(onLiberada).toHaveBeenCalled();
  });

  it("prende o foco, devolve ao fechar por Esc e é operável por teclado", async () => {
    // SPECSFY: SPEC-0039 US-005 FR-007 NFR-004 AC-020
    const { default: Dialogo } = await exigir<Modulo>("@/features/decisoes/LiberarColecaoDialog");
    simularFetch({});
    const onOpenChange = vi.fn();
    const user = userEvent.setup();
    render(<Dialogo open onOpenChange={onOpenChange} colecaoId="c1" abertas={3} />);

    const dialogo = screen.getByRole("dialog");
    await waitFor(() => expect(dialogo.contains(document.activeElement)).toBe(true));
    await user.tab();
    expect(dialogo.contains(document.activeElement)).toBe(true);

    await user.keyboard("{Escape}");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("sem contradições abertas não exibe o aviso de pendência", async () => {
    // SPECSFY: SPEC-0039 US-005 FR-007 NFR-004 AC-020
    const { default: Dialogo } = await exigir<Modulo>("@/features/decisoes/LiberarColecaoDialog");
    simularFetch({});
    render(<Dialogo open colecaoId="c1" abertas={0} />);

    expect(screen.getByRole("dialog")).not.toHaveTextContent(/contradições abertas/i);
    expect(screen.getByRole("button", { name: /^liberar para a base$/i })).toBeInTheDocument();
  });
});
