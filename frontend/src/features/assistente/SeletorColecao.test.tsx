import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SeletorColecao from "@/features/assistente/SeletorColecao";
import { json, simularFetch } from "@/features/colecoes/_apoio";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("SeletorColecao", () => {
  it("lista as coleções do projeto e devolve a escolhida", async () => {
    // SPECSFY: SPEC-0030 US-006 FR-013 AC-016
    simularFetch({
      "GET .*/api/v1/colecoes$": () =>
        json([
          { id: "c1", nome: "manuais", workspace_id: "w1", workspace_nome: "Clientes", documentos: 2 },
          { id: "c2", nome: "politicas", workspace_id: "w1", workspace_nome: "Clientes", documentos: 1 },
        ]),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<SeletorColecao value={null} onChange={onChange} />);

    const gatilho = screen.getByRole("combobox", { name: /coleção \(opcional\)/i });
    expect(gatilho).toHaveTextContent("Nenhuma");
    await user.click(gatilho);
    await user.click(await screen.findByRole("option", { name: "Clientes · manuais" }));

    expect(onChange).toHaveBeenCalledWith("c1");
    expect(screen.queryByText(/base/i)).toBeNull();
  });

  it("segue útil com só \"Nenhuma\" quando a leitura falha", async () => {
    // SPECSFY: SPEC-0030 US-006 FR-013 AC-016
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("rede"));
    render(<SeletorColecao value={null} onChange={vi.fn()} />);

    expect(await screen.findByRole("combobox", { name: /coleção \(opcional\)/i })).toHaveTextContent("Nenhuma");
  });
});
