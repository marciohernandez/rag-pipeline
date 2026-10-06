import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import BarraEtapas from "@/features/ingestao/BarraEtapas";

afterEach(cleanup);

describe("BarraEtapas", () => {
  it("marca a etapa atual e só libera as já alcançadas", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-013 FR-014 NFR-004 AC-015 AC-017
    const onIr = vi.fn();
    const user = userEvent.setup();
    render(<BarraEtapas etapa="divisao" maisAlta={1} onIr={onIr} />);

    expect(screen.getByRole("button", { name: /divisão/i })).toHaveAttribute("aria-current", "step");
    expect(screen.getByRole("button", { name: /prévia/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /publicação/i })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /arquivos/i }));
    expect(onIr).toHaveBeenCalledWith("arquivos");
  });

  it("lista as quatro etapas em ordem e é operável por teclado", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-013 FR-014 NFR-004 AC-015 AC-017
    const onIr = vi.fn();
    const user = userEvent.setup();
    render(<BarraEtapas etapa="publicacao" maisAlta={3} onIr={onIr} />);

    const nomes = screen.getAllByRole("button").map((b) => b.textContent);
    expect(nomes.join("|")).toMatch(/Arquivos.*Divisão.*Prévia.*Publicação/);
    await user.tab();
    expect(screen.getByRole("button", { name: /arquivos/i })).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onIr).toHaveBeenCalledWith("arquivos");
  });
});
