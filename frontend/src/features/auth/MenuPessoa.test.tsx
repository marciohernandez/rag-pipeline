import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace }),
}));

import { getToken, saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";
import { instalarMatchMedia, limparAmbienteTema } from "@/test/tema";

type Props = { nome: string; papel: string };
type Modulo = { default: ComponentType<Props> };

beforeEach(() => {
  replace.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-menu");
  instalarMatchMedia(false);
});

afterEach(() => {
  cleanup();
  limparAmbienteTema();
});

describe("MenuPessoa", () => {
  it("mostra o nome da pessoa, abre por teclado e devolve o foco ao gatilho ao fechar", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-009 AC-024
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    const user = userEvent.setup();
    render(<MenuPessoa nome="Ana Souza" papel="owner" />);

    const gatilho = screen.getByRole("button", { name: /ana souza/i });
    gatilho.focus();
    await user.keyboard("{Enter}");
    const trocarSenha = await screen.findByRole("menuitem", { name: /trocar senha/i });
    const sair = screen.getByRole("menuitem", { name: /sair/i });
    expect(screen.getByText("Owner")).toBeVisible();
    expect(trocarSenha).toHaveFocus();

    await user.keyboard("{ArrowDown}");
    expect(sair).toHaveFocus();
    await user.keyboard("{ArrowUp}");
    expect(trocarSenha).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("menuitem", { name: /sair/i })).not.toBeInTheDocument();
    expect(gatilho).toHaveFocus();
  });

  it("Sair limpa a sessão e volta ao Login", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-009 AC-024
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const user = userEvent.setup();
    render(<MenuPessoa nome="Ana Souza" papel="owner" />);

    await user.click(screen.getByRole("button", { name: /ana souza/i }));
    await user.click(await screen.findByRole("menuitem", { name: /sair/i }));

    expect(getToken()).toBeNull();
    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("Trocar senha abre o diálogo com senha atual, nova e confirmação", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-008 AC-024
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    const user = userEvent.setup();
    render(<MenuPessoa nome="Ana Souza" papel="owner" />);

    await user.click(screen.getByRole("button", { name: /ana souza/i }));
    await user.click(await screen.findByRole("menuitem", { name: /trocar senha/i }));

    const dialogo = await screen.findByRole("dialog", { name: /trocar senha/i });
    expect(dialogo).toBeInTheDocument();
    expect(screen.getByLabelText("Senha atual")).toBeInTheDocument();
    expect(screen.getByLabelText("Nova senha")).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar nova senha/i)).toBeInTheDocument();
  });

  it("test_menu_mostra_tres_opcoes_com_a_ativa_marcada", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-001 FR-008 NFR-003 AC-002
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    const user = userEvent.setup();
    render(<MenuPessoa nome="Ana Souza" papel="owner" />);

    await user.click(screen.getByRole("button", { name: /ana souza/i }));
    await screen.findByRole("menuitem", { name: /trocar senha/i });

    const grupo = screen.getByRole("group", { name: "Tema" });
    const opcoes = within(grupo).getAllByRole("menuitemradio");
    expect(opcoes.map((opcao) => opcao.textContent)).toEqual(["Claro", "Escuro", "Sistema"]);
    expect(opcoes.map((opcao) => opcao.getAttribute("aria-checked"))).toEqual([
      "false",
      "false",
      "true",
    ]);
  });

  it("test_grupo_tema_fica_entre_o_rotulo_da_pessoa_e_as_acoes_da_conta", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-001 FR-008 NFR-003 AC-002
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    const user = userEvent.setup();
    render(<MenuPessoa nome="Ana Souza" papel="owner" />);

    await user.click(screen.getByRole("button", { name: /ana souza/i }));
    const trocarSenha = await screen.findByRole("menuitem", { name: /trocar senha/i });
    const grupo = screen.getByRole("group", { name: "Tema" });

    expect(
      grupo.compareDocumentPosition(trocarSenha) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText("Owner")).toBeVisible();
  });

  it("test_trocar_tema_nao_altera_navegacao_nem_permissoes_do_menu", async () => {
    // SPECSFY: SPEC-0024 US-001 FR-002 NFR-004 AC-015
    const { default: MenuPessoa } = await exigir<Modulo>("@/features/auth/MenuPessoa");
    const user = userEvent.setup();
    render(<MenuPessoa nome="Bia Lima" papel="member" />);
    const gatilho = screen.getByRole("button", { name: /bia lima/i });
    const acoesDaConta = () =>
      screen.queryAllByRole("menuitem").map((item) => item.textContent);

    await user.click(gatilho);
    await screen.findByRole("menuitem", { name: /trocar senha/i });
    const antes = acoesDaConta();
    expect(antes).toEqual(["Trocar senha", "Sair"]);

    await user.click(await screen.findByRole("menuitemradio", { name: "Escuro" }));
    expect(document.documentElement).toHaveClass("dark");
    if (!screen.queryByRole("menuitem", { name: /sair/i })) await user.click(gatilho);
    await screen.findByRole("menuitem", { name: /sair/i });

    expect(acoesDaConta()).toEqual(antes);
    expect(screen.queryByRole("menuitem", { name: /pessoas/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
