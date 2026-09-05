import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Componente ainda não existe (RED de T030).
import FormularioConsulta from "@/features/execucoes/FormularioConsulta";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("FormularioConsulta — acessibilidade", () => {
  it("associa rótulo, anuncia carregamento e resultado, e não comunica os chunks só por cor", async () => {
    // SPECSFY: US-003 US-004 FR-005 FR-008 NFR-003 AC-018 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          resultado: "resposta",
          chunks_fontes: [{ chunk_id: "c-1", documento: "doc.md", trecho: "trecho" }],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const user = userEvent.setup();
    render(<FormularioConsulta baseId="base-1" />);

    const campo = screen.getByLabelText(/pergunta/i);
    expect(campo).toHaveAccessibleName();

    await user.type(campo, "pergunta");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    // região viva para anunciar carregamento/resultado
    const status = await screen.findByRole("status");
    await waitFor(() => expect(status).toHaveTextContent(/resposta/i));

    // cada chunk-fonte identificado por texto (documento), não só por cor
    expect(screen.getByText(/doc\.md/)).toBeInTheDocument();
  });
});
