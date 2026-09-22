import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";

import { saveSession } from "@/lib/session";
import { exigir } from "@/test/carregar";

interface Pessoa {
  id: string;
  nome: string;
}
interface DesativarProps {
  open: boolean;
  pessoa: Pessoa;
  acao: "desativar" | "reativar";
  bloqueio?: string;
  onOpenChange?: (aberto: boolean) => void;
  onDone?: () => void;
}
interface RedefinirProps {
  open: boolean;
  pessoa: Pessoa;
  onOpenChange?: (aberto: boolean) => void;
  onDone?: () => void;
}

const ana: Pessoa = { id: "pessoa-1", nome: "Ana Souza" };

beforeEach(() => {
  sessionStorage.clear();
  saveSession("sessao-opaca-owner");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("DesativarPessoaDialog", () => {
  it("mostra a pessoa alvo e a consequência antes de desativar", async () => {
    // SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 FR-015 AC-010 AC-025
    const { default: DesativarPessoaDialog } = await exigir<{
      default: ComponentType<DesativarProps>;
    }>("@/features/pessoas/DesativarPessoaDialog");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const onDone = vi.fn();
    const user = userEvent.setup();
    render(<DesativarPessoaDialog open pessoa={ana} acao="desativar" onDone={onDone} />);

    expect(screen.getByRole("dialog", { name: /desativar/i })).toBeInTheDocument();
    expect(screen.getByText(/ana souza/i)).toBeInTheDocument();
    expect(screen.getByText(/sessão .* termina/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^desativar$/i }));

    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/pessoas/pessoa-1/desativar");
    expect(init.method).toBe("POST");
  });

  it("reativa pela rota de reativar", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-015 AC-010 AC-025
    const { default: DesativarPessoaDialog } = await exigir<{
      default: ComponentType<DesativarProps>;
    }>("@/features/pessoas/DesativarPessoaDialog");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const user = userEvent.setup();
    render(<DesativarPessoaDialog open pessoa={ana} acao="reativar" />);

    await user.click(screen.getByRole("button", { name: /^reativar$/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalled());
    expect((fetchSpy.mock.calls[0] as [string])[0]).toBe("/api/v1/pessoas/pessoa-1/reativar");
  });

  it("não oferece desativar quando a regra do último owner ou de si mesma impede", async () => {
    // SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 AC-013 AC-025
    const { default: DesativarPessoaDialog } = await exigir<{
      default: ComponentType<DesativarProps>;
    }>("@/features/pessoas/DesativarPessoaDialog");
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(
      <DesativarPessoaDialog
        open
        pessoa={ana}
        acao="desativar"
        bloqueio="Este é o último owner ativo do tenant e não pode ser desativado."
      />,
    );

    expect(screen.getByText(/último owner ativo/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^desativar$/i })).toBeDisabled();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("RedefinirSenhaDialog", () => {
  it("pede a senha temporária, mostra a consequência e envia a redefinição", async () => {
    // SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 FR-015 AC-010 AC-025
    const { default: RedefinirSenhaDialog } = await exigir<{
      default: ComponentType<RedefinirProps>;
    }>("@/features/pessoas/RedefinirSenhaDialog");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    const onDone = vi.fn();
    const user = userEvent.setup();
    render(<RedefinirSenhaDialog open pessoa={ana} onDone={onDone} />);

    expect(screen.getByText(/ana souza/i)).toBeInTheDocument();
    expect(screen.getByText(/nova troca/i)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Senha temporária"), "senha-temporaria-123");
    await user.click(screen.getByRole("button", { name: /redefinir senha/i }));

    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/pessoas/pessoa-1/redefinir-senha");
    expect(JSON.parse(String(init.body))).toEqual({ senha_temporaria: "senha-temporaria-123" });
  });
});
