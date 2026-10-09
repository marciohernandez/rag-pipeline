import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ConsultaColecao from "@/features/colecoes/ConsultaColecao";
import { json, simularFetch } from "./_apoio";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ConsultaColecao", () => {
  it("consulta a coleção inteira e mostra o resultado, o autor e os chunks-fontes", async () => {
    // SPECSFY: SPEC-0030 US-006 FR-013 NFR-003 AC-016
    const chamadas = simularFetch({
      "POST .*/api/v1/colecoes/c1/query": () =>
        json({
          resultado: "A garantia cobre doze meses.",
          chunks_fontes: [
            { documento: "a.md", trecho: "Cláusula 7" },
            { documento: "b.md", trecho: "Cláusula 9" },
          ],
          criado_por: { id: "p1", nome: "Bruno Lima", desativada: true },
        }),
    });
    const user = userEvent.setup();
    render(<ConsultaColecao colecaoId="c1" />);

    expect(screen.getByRole("button", { name: /consultar/i })).toBeDisabled();
    await user.type(screen.getByLabelText(/pergunta/i), "O que diz?");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    expect(await screen.findByText("A garantia cobre doze meses.")).toBeInTheDocument();
    expect(screen.getByText(/consultada por bruno lima \(desativada\)/i)).toBeInTheDocument();
    expect(screen.getByText(/fonte: a\.md/i)).toBeInTheDocument();
    expect(screen.getByText(/fonte: b\.md/i)).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("A garantia cobre doze meses.");
    const [, init] = chamadas.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ pergunta: "O que diz?" });
  });

  it("mostra mensagem segura, preserva a pergunta e explica a coleção sem documentos", async () => {
    // SPECSFY: SPEC-0030 US-006 FR-013 NFR-001 AC-016
    simularFetch({
      "POST .*/api/v1/colecoes/c1/query": () => json({ detail: "endpoint interno recusou a chave qd-segredo" }, 502),
    });
    const user = userEvent.setup();
    render(<ConsultaColecao colecaoId="c1" />);

    const campo = screen.getByLabelText(/pergunta/i);
    await user.type(campo, "pergunta preservada");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Não foi possível consultar a coleção agora.");
    expect(alerta).not.toHaveTextContent(/qd-segredo|endpoint interno/);
    expect(campo).toHaveValue("pergunta preservada");
  });
});
