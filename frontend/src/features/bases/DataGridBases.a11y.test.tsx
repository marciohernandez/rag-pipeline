import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Componente ainda não existe (RED de T016).
import DataGridBases from "@/features/bases/DataGridBases";

const bases = [
  {
    id: "base-recente",
    origem: "preparada",
    status: "running",
    documentos: 1,
    chunks: 0,
    ultima_atualizacao: "2026-09-05T12:00:00Z",
  },
  {
    id: "base-antiga",
    origem: "upload",
    status: "succeeded",
    documentos: 2,
    chunks: 8,
    ultima_atualizacao: "2026-09-04T12:00:00Z",
  },
];

afterEach(() => {
  cleanup();
  push.mockReset();
});

describe("DataGridBases — acessibilidade", () => {
  it("mantém a coluna ID visível e abre o detalhe da linha por Enter", async () => {
    // SPECSFY: US-002 FR-002 FR-004 NFR-003 AC-017 (SPEC-0013)
    const user = userEvent.setup();
    render(<DataGridBases bases={bases} />);

    expect(
      screen.getByRole("columnheader", { name: /id/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("base-recente")).toBeInTheDocument();

    const linha = screen.getByRole("row", { name: /base-recente/i });
    linha.focus();
    await user.keyboard("{Enter}");

    expect(push).toHaveBeenCalledWith(
      expect.stringContaining("base-recente"),
    );
  });

  it("mantém a visualização de bases sem ações de escrita para member", () => {
    // SPECSFY: SPEC-0019 US-004 FR-008 AC-017
    render(<DataGridBases bases={bases} papel="member" />);

    expect(screen.getByText("base-recente")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apagar/i })).not.toBeInTheDocument();
  });
});
