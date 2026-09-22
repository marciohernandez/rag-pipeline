import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import { exigir } from "@/test/carregar";

interface Pessoa {
  id: string;
  nome: string;
  email: string;
  papel: string;
  situacao: string;
  precisa_trocar_senha: boolean;
}
interface Props {
  pessoas: Pessoa[];
  carregando?: boolean;
  onEditar?: (pessoa: Pessoa) => void;
  onAlternarSituacao?: (pessoa: Pessoa) => void;
}
type Modulo = { default: ComponentType<Props> };

const pessoas: Pessoa[] = [
  {
    id: "pessoa-1",
    nome: "Ana Souza",
    email: "ana@exemplo.com",
    papel: "owner",
    situacao: "ativa",
    precisa_trocar_senha: false,
  },
  {
    id: "pessoa-2",
    nome: "Bruno Lima",
    email: "bruno@exemplo.com",
    papel: "member",
    situacao: "desativada",
    precisa_trocar_senha: true,
  },
];

afterEach(() => {
  cleanup();
  push.mockReset();
});

describe("DataGridPessoas", () => {
  it("mostra ID, nome, e-mail, papel e situação, e abre o detalhe pela linha inteira por teclado", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-025
    const { default: DataGridPessoas } = await exigir<Modulo>("@/features/pessoas/DataGridPessoas");
    const user = userEvent.setup();
    render(<DataGridPessoas pessoas={pessoas} />);

    for (const cabecalho of ["ID", "Nome", "E-mail", "Papel", "Situação"]) {
      expect(screen.getByRole("columnheader", { name: cabecalho })).toBeInTheDocument();
    }
    expect(screen.getByText("pessoa-1")).toBeInTheDocument();
    const linha = screen.getByRole("row", { name: /ana souza/i });
    linha.focus();
    await user.keyboard("{Enter}");
    expect(push).toHaveBeenCalledWith("/pessoas/pessoa-1");

    const desativada = screen.getByRole("row", { name: /bruno lima/i });
    expect(within(desativada).getByText("Desativada")).toBeInTheDocument();
  });

  it("oferece Editar e Desativar ou Reativar independentes da linha e nunca Apagar", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-025
    const { default: DataGridPessoas } = await exigir<Modulo>("@/features/pessoas/DataGridPessoas");
    const onEditar = vi.fn();
    const onAlternarSituacao = vi.fn();
    const user = userEvent.setup();
    render(
      <DataGridPessoas
        pessoas={pessoas}
        onEditar={onEditar}
        onAlternarSituacao={onAlternarSituacao}
      />,
    );

    await user.click(screen.getByRole("button", { name: /editar ana souza/i }));
    expect(onEditar).toHaveBeenCalledWith(pessoas[0]);
    await user.click(screen.getByRole("button", { name: /desativar ana souza/i }));
    expect(onAlternarSituacao).toHaveBeenCalledWith(pessoas[0]);
    await user.click(screen.getByRole("button", { name: /reativar bruno lima/i }));
    expect(onAlternarSituacao).toHaveBeenCalledWith(pessoas[1]);
    expect(push).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: /apagar|excluir/i })).not.toBeInTheDocument();
  });

  it("mostra a estrutura de carregamento e mantém a lista rolável na horizontal em tela pequena", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-015 NFR-005 AC-025 AC-026
    const { default: DataGridPessoas } = await exigir<Modulo>("@/features/pessoas/DataGridPessoas");
    const { rerender } = render(<DataGridPessoas pessoas={[]} carregando />);
    expect(screen.getByRole("table")).toHaveAttribute("aria-busy", "true");

    rerender(<DataGridPessoas pessoas={pessoas} />);
    const regiao = screen.getByRole("table").closest("[class*='overflow-x-auto']");
    expect(regiao).not.toBeNull();
    expect(screen.getByRole("columnheader", { name: "ID" })).toBeInTheDocument();
  });
});
