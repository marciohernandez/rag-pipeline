import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import { exigir } from "@/test/carregar";

interface Conexao {
  id: string;
  nome: string;
  tipo: string;
  situacao: string;
  segredo_definido: boolean;
  segredo_mascara: string;
  em_uso: number;
}
interface Props {
  conexoes: Conexao[];
  carregando?: boolean;
  onEditar?: (conexao: Conexao) => void;
  onAlternarSituacao?: (conexao: Conexao) => void;
  onExcluir?: (conexao: Conexao) => void;
}
type Modulo = { default: ComponentType<Props> };

const conexoes: Conexao[] = [
  { id: "con-1", nome: "OpenAI principal", tipo: "embeddings_openai", situacao: "ativa", segredo_definido: true, segredo_mascara: "••••••••", em_uso: 2 },
  { id: "con-2", nome: "Qdrant produção", tipo: "qdrant", situacao: "ativa", segredo_definido: true, segredo_mascara: "••••••••", em_uso: 0 },
  { id: "con-3", nome: "Qdrant antigo", tipo: "qdrant", situacao: "desativada", segredo_definido: false, segredo_mascara: "", em_uso: 0 },
];

afterEach(() => {
  cleanup();
  push.mockReset();
});

describe("DataGridConexoes", () => {
  it("mostra a coluna ID, abre o detalhe pela linha inteira por teclado e não revela a chave", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018
    const { default: DataGridConexoes } = await exigir<Modulo>("@/features/conexoes/DataGridConexoes");
    const user = userEvent.setup();
    render(<DataGridConexoes conexoes={conexoes} />);

    for (const cabecalho of ["ID", "Nome", "Tipo", "Situação"]) {
      expect(screen.getByRole("columnheader", { name: cabecalho })).toBeInTheDocument();
    }
    expect(screen.getByText("con-1")).toBeInTheDocument();
    const linha = screen.getByRole("row", { name: /openai principal/i });
    linha.focus();
    await user.keyboard("{Enter}");
    expect(push).toHaveBeenCalledWith("/conexoes/con-1");
    expect(screen.getAllByText("••••••••").length).toBeGreaterThan(0);
    expect(screen.queryByText(/sk-/)).not.toBeInTheDocument();
  });

  it("oferece editar, desativar ou reativar e excluir como ações independentes da linha", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018
    const { default: DataGridConexoes } = await exigir<Modulo>("@/features/conexoes/DataGridConexoes");
    const onEditar = vi.fn();
    const onAlternarSituacao = vi.fn();
    const onExcluir = vi.fn();
    const user = userEvent.setup();
    render(
      <DataGridConexoes
        conexoes={conexoes}
        onEditar={onEditar}
        onAlternarSituacao={onAlternarSituacao}
        onExcluir={onExcluir}
      />,
    );

    await user.click(screen.getByRole("button", { name: /editar openai principal/i }));
    expect(onEditar).toHaveBeenCalledWith(conexoes[0]);
    await user.click(screen.getByRole("button", { name: /desativar qdrant produção/i }));
    expect(onAlternarSituacao).toHaveBeenCalledWith(conexoes[1]);
    await user.click(screen.getByRole("button", { name: /reativar qdrant antigo/i }));
    expect(onAlternarSituacao).toHaveBeenCalledWith(conexoes[2]);
    await user.click(screen.getByRole("button", { name: /excluir qdrant produção/i }));
    expect(onExcluir).toHaveBeenCalledWith(conexoes[1]);
    expect(push).not.toHaveBeenCalled();
    const desativada = screen.getByRole("row", { name: /qdrant antigo/i });
    expect(within(desativada).getByText("Desativada")).toBeInTheDocument();
  });

  it("anuncia o carregamento e mantém a lista rolável em tela pequena", async () => {
    // SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018
    const { default: DataGridConexoes } = await exigir<Modulo>("@/features/conexoes/DataGridConexoes");
    const { rerender } = render(<DataGridConexoes conexoes={[]} carregando />);
    expect(screen.getByRole("table")).toHaveAttribute("aria-busy", "true");

    rerender(<DataGridConexoes conexoes={conexoes} />);
    expect(screen.getByRole("table")).not.toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("table").parentElement).toHaveClass("overflow-x-auto");
  });
});
