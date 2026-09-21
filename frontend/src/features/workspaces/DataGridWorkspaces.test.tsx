import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import DataGridWorkspaces from "@/features/workspaces/DataGridWorkspaces";

const workspaces = [
  { id: "workspace-1", nome: "Banda Larga PF — Vivo — Gold" },
  { id: "workspace-2", nome: "Atendimento B2B" },
];

afterEach(() => {
  cleanup();
  push.mockReset();
});

describe("DataGridWorkspaces", () => {
  it("mostra a estrutura de loading", () => {
    render(<DataGridWorkspaces workspaces={[]} carregando />);

    expect(screen.getByText(/carregando workspaces/i)).toBeInTheDocument();
    expect(screen.getByRole("table")).toHaveAttribute("aria-busy", "true");
  });

  it("explica o vazio conforme a permissão de criação", () => {
    render(<DataGridWorkspaces workspaces={[]} podeCriar />);

    expect(screen.getByText("Nenhum Workspace ainda")).toBeInTheDocument();
    expect(screen.getByText(/crie o primeiro workspace/i)).toBeInTheDocument();
  });

  it("mantém ID visível e abre o detalhe por Enter", async () => {
    // SPECSFY: SPEC-0019 US-001 US-004 FR-001 FR-008 AC-001 AC-017
    const user = userEvent.setup();
    render(<DataGridWorkspaces workspaces={workspaces} />);

    expect(screen.getByRole("columnheader", { name: "ID" })).toBeInTheDocument();
    expect(screen.getByText("workspace-1")).toBeInTheDocument();

    const linha = screen.getByRole("row", { name: /banda larga pf/i });
    linha.focus();
    await user.keyboard("{Enter}");

    expect(push).toHaveBeenCalledWith("/workspaces/workspace-1");
  });

  it("abre o detalhe por Espaço sem rolar a página", async () => {
    const user = userEvent.setup();
    render(<DataGridWorkspaces workspaces={workspaces} />);

    const linha = screen.getByRole("row", { name: /atendimento b2b/i });
    linha.focus();
    await user.keyboard(" ");

    expect(push).toHaveBeenCalledWith("/workspaces/workspace-2");
  });
});
