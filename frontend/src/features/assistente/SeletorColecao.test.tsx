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
    expect(gatilho).toHaveTextContent("Todas as coleções");
    await user.click(gatilho);
    await user.click(await screen.findByRole("option", { name: "Clientes · manuais" }));

    expect(onChange).toHaveBeenCalledWith("c1");
    expect(screen.queryByText(/base/i)).toBeNull();
  });

  it("segue útil com só \"Todas as coleções\" quando a leitura falha", async () => {
    // SPECSFY: SPEC-0030 US-006 FR-013 AC-016
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("rede"));
    render(<SeletorColecao value={null} onChange={vi.fn()} />);

    expect(await screen.findByRole("combobox", { name: /coleção \(opcional\)/i })).toHaveTextContent("Todas as coleções");
  });

  it("começa em Todas as coleções, filtra pelo teclado e limpa o filtro", async () => {
    // SPECSFY: SPEC-0031 US-001 FR-001 FR-007 NFR-003 AC-002
    simularFetch({
      "GET .*/api/v1/colecoes$": () =>
        json([
          { id: "c1", nome: "manuais", workspace_id: "w1", workspace_nome: "Clientes", documentos: 2 },
          { id: "c2", nome: "politicas", workspace_id: "w1", workspace_nome: "Clientes", documentos: 1 },
        ]),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(<SeletorColecao value={null} onChange={onChange} />);

    const gatilho = await screen.findByRole("combobox", { name: /filtrar por coleção \(opcional\)/i });
    expect(gatilho).toHaveTextContent("Todas as coleções");

    gatilho.focus();
    await user.keyboard("{Enter}");
    const opcao = await screen.findByRole("option", { name: "Clientes · politicas" });
    opcao.focus();
    await user.keyboard("{Enter}");
    expect(onChange).toHaveBeenCalledWith("c2");

    rerender(<SeletorColecao value="c2" onChange={onChange} />);
    const limpar = await screen.findByRole("button", { name: /limpar filtro/i });
    limpar.focus();
    await user.keyboard("{Enter}");
    expect(onChange).toHaveBeenLastCalledWith(null);
  });
});
