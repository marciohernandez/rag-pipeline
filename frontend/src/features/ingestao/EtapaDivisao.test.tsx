import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import EtapaDivisao from "@/features/ingestao/EtapaDivisao";
import { PADROES_FALLBACK } from "@/lib/ingestao";

const base = {
  arquivos: [] as File[],
  padroes: PADROES_FALLBACK,
  splitter: "header",
  tamanho: "1000",
  overlap: "200",
  tentativas: 0,
  onAlterar: vi.fn(),
};

afterEach(cleanup);

describe("EtapaDivisao", () => {
  it("mostra os campos pré-preenchidos com ajuda e as duas estratégias", () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    render(<EtapaDivisao {...base} />);

    expect(screen.getByLabelText("Tamanho do chunk")).toHaveValue(1000);
    expect(screen.getByLabelText("Overlap")).toHaveValue(200);
    expect(screen.getByLabelText("Estratégia de divisão")).toHaveValue("header");
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual([
      "Markdown por cabeçalhos",
      "Recursivo por caracteres",
    ]);
    expect(screen.getByText(/de 200 a 4000/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("mostra o erro abaixo do campo e foca o primeiro inválido ao tentar avançar", () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    const { rerender } = render(<EtapaDivisao {...base} tamanho="5000" overlap="3000" />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    rerender(<EtapaDivisao {...base} tamanho="5000" overlap="3000" tentativas={1} />);

    expect(screen.getByText(/máximo de 4000/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Tamanho do chunk")).toHaveFocus();
    expect(screen.getByLabelText("Tamanho do chunk")).toHaveAttribute("aria-invalid", "true");

    rerender(<EtapaDivisao {...base} tamanho="800" overlap="600" tentativas={2} />);
    expect(screen.getByText(/até a metade do tamanho \(400\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Overlap")).toHaveFocus();
  });

  it("avisa os arquivos com configuração própria no frontmatter", async () => {
    // SPECSFY: SPEC-0026 US-002 FR-006 FR-007 FR-014 NFR-004 AC-015 AC-017
    const qa = new File(["---\nsplitter: qa\n---\nP: Um?\nR: Um."], "qa.md");
    const comum = new File(["# Comum\n\nTexto."], "comum.md");
    const user = userEvent.setup();
    render(<EtapaDivisao {...base} arquivos={[qa, comum]} />);

    expect(await screen.findByText(/configuração própria no frontmatter/i)).toHaveTextContent("qa.md");
    expect(screen.getByText(/configuração própria no frontmatter/i)).not.toHaveTextContent("comum.md");
    await user.selectOptions(screen.getByLabelText("Estratégia de divisão"), "recursive");
    expect(base.onAlterar).toHaveBeenCalledWith("splitter", "recursive");
  });
});
