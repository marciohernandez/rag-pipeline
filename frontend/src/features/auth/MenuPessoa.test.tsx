import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace }),
}));

import { getToken, saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Props = { nome: string; papel: string };
type Modulo = { default: ComponentType<Props> };

beforeEach(() => {
  replace.mockReset();
  sessionStorage.clear();
  saveSession("sessao-opaca-menu");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
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
    expect(await screen.findByRole("menuitem", { name: /trocar senha/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /sair/i })).toBeInTheDocument();

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
});
