import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { exigir } from "@/test/carregar";

import type { FonteDaResposta } from "./useAssistente";

type Modulo = typeof import("./FontesDaResposta");

afterEach(cleanup);

const fontes: FonteDaResposta[] = [
  {
    tipo: "documento",
    rotulo: "manual.md — Manuais",
    colecao_id: "c1",
    documento: "manual.md",
    envio_id: null,
    rota: "/workspaces/w1/colecoes/c1",
  },
  {
    tipo: "envio",
    rotulo: "Envio de manual.md — Manuais",
    colecao_id: "c1",
    documento: null,
    envio_id: "e1",
    rota: "/envios/e1",
  },
];

describe("FontesDaResposta", () => {
  it("abre o destino da fonte pelo teclado com rótulo que identifica o destino", async () => {
    // SPECSFY: SPEC-0031 US-004 FR-006 FR-008 NFR-003 AC-012
    const { default: FontesDaResposta } = await exigir<Modulo>("@/features/assistente/FontesDaResposta");
    const user = userEvent.setup();
    render(<FontesDaResposta fontes={fontes} />);

    const documento = screen.getByRole("link", { name: "Abrir documento manual.md da coleção Manuais" });
    expect(documento).toHaveAttribute("href", "/workspaces/w1/colecoes/c1");
    const envio = screen.getByRole("link", { name: /abrir envio/i });
    expect(envio).toHaveAttribute("href", "/envios/e1");

    await user.tab();
    expect(documento).toHaveFocus();
    await user.tab();
    expect(envio).toHaveFocus();
  });
});
