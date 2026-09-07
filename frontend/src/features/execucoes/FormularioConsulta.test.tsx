import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Componente ainda não existe (RED de T028/T029).
import FormularioConsulta from "@/features/execucoes/FormularioConsulta";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("FormularioConsulta", () => {
  it("mostra o resultado e os chunks-fontes identificados pelo documento de origem", async () => {
    // SPECSFY: US-004 FR-008 AC-012 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          resultado: "O plano Turbo tem 500 Mbps.",
          chunks_fontes: [
            { chunk_id: "c-1", documento: "planos.md", trecho: "Plano Turbo: 500 Mbps." },
          ],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const user = userEvent.setup();
    render(<FormularioConsulta baseId="base-1" />);

    await user.type(screen.getByLabelText(/pergunta/i), "Qual a velocidade do Turbo?");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    // resultado (exato — o trecho do chunk também contém "500 Mbps")
    expect(
      await screen.findByText("O plano Turbo tem 500 Mbps."),
    ).toBeInTheDocument();
    // chunk-fonte identificado pelo documento de origem
    expect(screen.getByText(/planos\.md/)).toBeInTheDocument();
  });

  it("em falha mostra erro seguro sem detalhe do provedor e preserva a pergunta", async () => {
    // SPECSFY: US-004 FR-008 AC-013 (SPEC-0013)
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"falha ao consultar a base"}', { status: 502 }),
    );
    const user = userEvent.setup();
    render(<FormularioConsulta baseId="base-1" />);

    const campo = screen.getByLabelText(/pergunta/i);
    await user.type(campo, "pergunta que vai falhar");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent ?? "").not.toMatch(/provider|openai|qdrant|embedding/i);
    await waitFor(() => expect(campo).toHaveValue("pergunta que vai falhar"));
  });
});
