import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import DetalheEnvio from "@/features/envios/DetalheEnvio";
import { json, simularFetch } from "@/features/colecoes/_apoio";

const base = {
  id: "env-1",
  colecao: { id: "c1", nome: "manuais", workspace_id: "w1" },
  arquivos: ["a.md", "b.md"],
  processamento: { splitter: "header" },
  situacao: "succeeded",
  etapa: "concluido",
  previstos: 12,
  inseridos: 7,
  mantidos: 5,
  removidos: 3,
  erro: null,
  iniciado_em: "2026-10-09T10:00:00Z",
  concluido_em: "2026-10-09T10:01:00Z",
  criado_por: { id: "p1", nome: "Ana Souza", desativada: false },
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("DetalheEnvio", () => {
  it("mostra etapa, contagens, arquivos e autor de um envio concluído", () => {
    // SPECSFY: SPEC-0030 US-003 FR-012 NFR-003 AC-009
    render(<DetalheEnvio envio={base} papel="member" />);

    expect(screen.getByText("Concluído")).toBeInTheDocument();
    for (const [rotulo, valor] of [["Previstos", "12"], ["Inseridos", "7"], ["Mantidos", "5"], ["Removidos", "3"]]) {
      expect(screen.getByText(rotulo).nextElementSibling).toHaveTextContent(valor);
    }
    expect(screen.getByText("a.md, b.md")).toBeInTheDocument();
    expect(screen.getByText(/iniciado por ana souza/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repetir/i })).toBeNull();
  });

  it("oferece Repetir só a owner e admin num envio que falhou, sem expor detalhe", async () => {
    // SPECSFY: SPEC-0030 US-002 FR-012 FR-015 AC-007 AC-009
    const chamadas = simularFetch({ "POST .*/api/v1/envios/env-1/retry": () => json({}, 202) });
    const onRepetido = vi.fn();
    const falhou = { ...base, situacao: "failed", erro: "Falha ao processar o envio; ver logs do worker para detalhes." };
    const user = userEvent.setup();
    const { rerender } = render(<DetalheEnvio envio={falhou} papel="member" />);
    expect(screen.queryByRole("button", { name: /repetir/i })).toBeNull();

    rerender(<DetalheEnvio envio={falhou} papel="admin" onRepetido={onRepetido} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Falha ao processar o envio");
    await user.click(screen.getByRole("button", { name: /repetir/i }));

    await waitFor(() => expect(onRepetido).toHaveBeenCalledTimes(1));
    expect(chamadas).toHaveBeenCalledTimes(1);
  });

  it("anuncia o envio em andamento e mostra erro seguro quando Repetir falha", async () => {
    // SPECSFY: SPEC-0030 US-003 FR-012 NFR-003 AC-009
    const { rerender } = render(<DetalheEnvio envio={{ ...base, situacao: "running" }} papel="owner" />);
    expect(screen.getByRole("status")).toHaveTextContent(/envio em andamento/i);

    simularFetch({ "POST .*/retry": () => json({ detail: "x" }, 500) });
    rerender(<DetalheEnvio envio={{ ...base, situacao: "failed", erro: "falhou" }} papel="owner" />);
    await userEvent.setup().click(screen.getByRole("button", { name: /repetir/i }));
    expect(await screen.findByText("Não foi possível repetir o envio. Tente novamente.")).toBeInTheDocument();
  });
});
