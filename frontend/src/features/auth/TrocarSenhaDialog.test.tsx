import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

import { getToken, saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

type Props = { open: boolean; onOpenChange?: (aberto: boolean) => void; onChanged?: () => void };
type Modulo = { default: ComponentType<Props> };

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-atual");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("TrocarSenhaDialog", () => {
  it("troca a própria senha com senha atual, nova e confirmação e mantém a sessão atual", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-005 FR-014 AC-007 AC-008 AC-024
    const { default: TrocarSenhaDialog } = await exigir<Modulo>(
      "@/features/auth/TrocarSenhaDialog",
    );
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const onChanged = vi.fn();
    const onOpenChange = vi.fn();
    const user = userEvent.setup();
    render(<TrocarSenhaDialog open onChanged={onChanged} onOpenChange={onOpenChange} />);

    expect(screen.getByRole("dialog", { name: /trocar senha/i })).toBeInTheDocument();
    const atual = screen.getByLabelText("Senha atual");
    const nova = screen.getByLabelText("Nova senha");
    expect(atual).toHaveAttribute("autocomplete", "current-password");
    expect(nova).toHaveAttribute("autocomplete", "new-password");

    await user.type(atual, "senha-atual-123");
    await user.type(nova, "senha-nova-valida-1");
    await user.type(screen.getByLabelText(/confirmar nova senha/i), "senha-nova-valida-1");
    await user.click(screen.getByRole("button", { name: /trocar senha/i }));

    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/senha");
    expect(JSON.parse(String(init.body))).toEqual({
      senha_atual: "senha-atual-123",
      nova_senha: "senha-nova-valida-1",
    });
    expect(getToken()).toBe("sessao-opaca-atual");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("mostra o erro de senha atual incorreta abaixo do campo e devolve o foco a ele", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-005 FR-014 AC-007 AC-024
    const { default: TrocarSenhaDialog } = await exigir<Modulo>(
      "@/features/auth/TrocarSenhaDialog",
    );
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response('{"detail":"Senha atual incorreta."}', {
        status: 422,
        headers: { "content-type": "application/json" },
      }),
    );
    const onChanged = vi.fn();
    const user = userEvent.setup();
    render(<TrocarSenhaDialog open onChanged={onChanged} />);

    const atual = screen.getByLabelText("Senha atual");
    await user.type(atual, "senha-errada-123");
    await user.type(screen.getByLabelText("Nova senha"), "senha-nova-valida-1");
    await user.type(screen.getByLabelText(/confirmar nova senha/i), "senha-nova-valida-1");
    await user.click(screen.getByRole("button", { name: /trocar senha/i }));

    expect(await screen.findByText(/senha atual incorreta/i)).toBeInTheDocument();
    expect(atual).toHaveAttribute("aria-invalid", "true");
    expect(atual).toHaveAttribute("aria-describedby", "erro-senha-atual");
    expect(atual).toHaveFocus();
    expect(onChanged).not.toHaveBeenCalled();
  });

  it("permite inspecionar as senhas e associa a regra local ao primeiro erro", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-005 FR-014 NFR-005 AC-007 AC-024
    const { default: TrocarSenhaDialog } = await exigir<Modulo>(
      "@/features/auth/TrocarSenhaDialog",
    );
    const user = userEvent.setup();
    render(<TrocarSenhaDialog open />);

    const atual = screen.getByLabelText("Senha atual");
    const nova = screen.getByLabelText("Nova senha");
    const confirmacao = screen.getByLabelText(/confirmar nova senha/i);
    expect(atual).toHaveAttribute("type", "password");

    await user.click(screen.getByRole("checkbox", { name: /mostrar senhas/i }));
    expect(atual).toHaveAttribute("type", "text");
    expect(nova).toHaveAttribute("type", "text");
    expect(confirmacao).toHaveAttribute("type", "text");

    await user.click(screen.getByRole("button", { name: /trocar senha/i }));
    expect(await screen.findByText(/pelo menos 10 caracteres/i)).toBeInTheDocument();
    expect(nova).toHaveFocus();
    expect(nova).toHaveAttribute(
      "aria-describedby",
      "regra-troca-senha erro-troca-nova",
    );
  });

  it("bloqueia o fechamento durante o envio e limpa os valores após trocar", async () => {
    // SPECSFY: SPEC-0020 US-002 FR-005 FR-014 NFR-005 AC-007 AC-008
    const { default: TrocarSenhaDialog } = await exigir<Modulo>(
      "@/features/auth/TrocarSenhaDialog",
    );
    let concluir!: (resposta: Response) => void;
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise<Response>((resolve) => { concluir = resolve; }),
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();
    render(<TrocarSenhaDialog open onOpenChange={onOpenChange} />);

    await user.type(screen.getByLabelText("Senha atual"), "senha-atual-123");
    await user.type(screen.getByLabelText("Nova senha"), "senha-nova-valida-1");
    await user.type(screen.getByLabelText(/confirmar nova senha/i), "senha-nova-valida-1");
    await user.click(screen.getByRole("button", { name: /trocar senha/i }));

    expect(screen.getByRole("button", { name: /trocando/i })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /fechar/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancelar/i })).toBeDisabled();

    concluir(new Response(null, { status: 204 }));
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(screen.getByLabelText("Senha atual")).toHaveValue("");
    expect(screen.getByLabelText("Nova senha")).toHaveValue("");
    expect(screen.getByLabelText(/confirmar nova senha/i)).toHaveValue("");
  });
});
