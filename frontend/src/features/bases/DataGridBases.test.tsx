import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import DataGridBases from "@/features/bases/DataGridBases";
import FormularioConsulta from "@/features/execucoes/FormularioConsulta";
import PainelProgresso from "@/features/execucoes/PainelProgresso";
import DataGridWorkspaces from "@/features/workspaces/DataGridWorkspaces";

const ana = { id: "pessoa-1", nome: "Ana Souza", desativada: false };
const carla = { id: "pessoa-2", nome: "Carla Dias", desativada: true };

const bases = [
  { id: "base-1", origem: "upload", status: "succeeded", documentos: 2, chunks: 8, ultima_atualizacao: "2026-09-20T10:00:00Z", criado_por: ana },
  { id: "base-2", origem: "upload", status: "succeeded", documentos: 1, chunks: 3, ultima_atualizacao: "2026-09-19T10:00:00Z", criado_por: null },
  { id: "base-3", origem: "preparada", status: "failed", documentos: 1, chunks: 0, ultima_atualizacao: "2026-09-18T10:00:00Z", criado_por: carla },
];
const workspaces = [
  { id: "workspace-1", nome: "Vivo", criado_por: ana },
  { id: "workspace-2", nome: "Anterior", criado_por: null },
  { id: "workspace-3", nome: "Da Carla", criado_por: carla },
];
const execucao = {
  id: "exec-1", base_id: "base-1", situacao: "succeeded", etapa: "concluido",
  previstos: 1, inseridos: 1, mantidos: 0, removidos: 0, erro: null,
  iniciado_em: "2026-09-20T10:00:00Z", concluido_em: "2026-09-20T10:01:00Z",
  criado_por: { id: "pessoa-3", nome: "Bruno Lima", desativada: false },
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  push.mockReset();
});

describe("Autoria nas listas e detalhes", () => {
  it("lista de Bases mostra Criada por, Autor não identificado e o autor desativado sem esconder o ID", async () => {
    // SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017
    const user = userEvent.setup();
    render(<DataGridBases bases={bases} />);

    expect(screen.getByRole("columnheader", { name: "ID" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Criada por" })).toBeInTheDocument();
    expect(screen.getByText("Ana Souza")).toBeInTheDocument();
    expect(screen.getByText("Autor não identificado")).toBeInTheDocument();
    expect(screen.getByText(/carla dias \(desativada\)/i)).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")[0]).toHaveTextContent("ID");
    expect(screen.getByRole("table")).toHaveClass("min-w-[72rem]");
    expect(screen.getByRole("table").parentElement).toHaveClass("overflow-x-auto");

    const linha = screen.getByRole("row", { name: /base-1/i });
    linha.focus();
    await user.keyboard("{Enter}");
    expect(push).toHaveBeenCalledWith("/execucoes/base-1");
  });

  it("lista de Workspaces mostra Criada por com o mesmo tratamento", async () => {
    // SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017
    render(<DataGridWorkspaces workspaces={workspaces} />);

    expect(screen.getByRole("columnheader", { name: "Criada por" })).toBeInTheDocument();
    expect(screen.getByText("Ana Souza")).toBeInTheDocument();
    expect(screen.getByText("Autor não identificado")).toBeInTheDocument();
    expect(screen.getByText(/carla dias \(desativada\)/i)).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")[0]).toHaveTextContent("ID");
    expect(screen.getByRole("table")).toHaveClass("min-w-[48rem]");
  });

  it("progresso da Execução mostra Iniciada por", async () => {
    // SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017
    render(<PainelProgresso execucao={execucao} papel="owner" />);

    expect(screen.getByText(/iniciada por/i)).toBeInTheDocument();
    expect(screen.getByText(/bruno lima/i)).toBeInTheDocument();
  });

  it("progresso identifica autora desativada e autoria histórica ausente", () => {
    // SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017
    const { rerender } = render(
      <PainelProgresso
        execucao={{ ...execucao, criado_por: { ...carla, nome: "Carla Dias" } }}
        papel="owner"
      />,
    );
    expect(screen.getByText(/iniciada por carla dias \(desativada\)/i)).toBeInTheDocument();

    rerender(<PainelProgresso execucao={{ ...execucao, criado_por: null }} papel="owner" />);
    expect(screen.getByText(/iniciada por autor não identificado/i)).toBeInTheDocument();
  });

  it("resultado da Consulta mostra Consultada por", async () => {
    // SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          resultado: "Resposta.",
          chunks_fontes: [],
          criado_por: { id: "pessoa-3", nome: "Bruno Lima", desativada: true },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const user = userEvent.setup();
    render(<FormularioConsulta baseId="base-1" />);

    await user.type(screen.getByLabelText(/pergunta/i), "O que diz?");
    await user.click(screen.getByRole("button", { name: /consultar/i }));

    await waitFor(() => expect(screen.getByText(/consultada por/i)).toBeInTheDocument());
    expect(screen.getByText(/bruno lima \(desativada\)/i)).toBeInTheDocument();
  });
});
