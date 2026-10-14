import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { exigir } from "@/test/carregar";

type Aviso = { codigo: string; pagina: number | null; mensagem: string };
type Modulo = { default: ComponentType<{ avisos: Aviso[] }> };

const POUCO_TEXTO: Aviso = {
  codigo: "ocr_pouco_texto",
  pagina: 2,
  mensagem: "A página 2 foi lida por OCR, mas devolveu pouco texto.",
};
const LIMITE: Aviso = {
  codigo: "ocr_limite_de_paginas",
  pagina: null,
  mensagem: "3 páginas não foram lidas por OCR por causa do limite.",
};

afterEach(cleanup);

async function carregarSelo() {
  const { default: Selo } = await exigir<Modulo>("@/features/conversao/SeloRevisarDocumento");
  return Selo;
}

describe("Selo Revisar do documento de conversão", () => {
  it("mostra o selo Revisar com o motivo e a página no nome acessível", async () => {
    // SPECSFY: SPEC-0033 US-002 FR-008 AC-004
    const Selo = await carregarSelo();
    render(<Selo avisos={[POUCO_TEXTO]} />);

    const selo = screen.getByRole("button", { name: /revisar/i });
    expect(selo).toHaveAccessibleName(expect.stringContaining("página 2"));
    expect(screen.queryByText("ocr_pouco_texto")).toBeNull();
  });

  it("não renderiza nada quando o documento não tem aviso", async () => {
    // SPECSFY: SPEC-0033 US-002 FR-008 AC-006
    const Selo = await carregarSelo();
    const { container } = render(<Selo avisos={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("é alcançável por teclado e resume vários avisos sem mostrar o código cru", async () => {
    // SPECSFY: SPEC-0033 US-002 FR-008 AC-012
    const Selo = await carregarSelo();
    render(<Selo avisos={[POUCO_TEXTO, LIMITE]} />);

    await userEvent.tab();

    const selo = screen.getByRole("button", { name: /revisar/i });
    expect(selo).toHaveFocus();
    expect(selo).toHaveAccessibleName(expect.stringContaining("3 páginas não foram lidas"));
    expect(screen.queryByText("ocr_limite_de_paginas")).toBeNull();
  });
});
